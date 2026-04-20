#!/usr/bin/env python3
"""Compute concern-alignment aggregate metrics per Skill 4.

This script is designed to be robust to two common repo layouts:

Layout A (flat):
  <root>/
    official/
    agentic/<version>/<method>/*.yaml
    match_graphs/<version>/<method>/*.yaml
    papers/*.pdf   (optional; used only for lightweight groundedness diagnostics)

Layout B (nested under a calibration subtree):
  <root>/
    calibration/concern_alignment/
      official/
      agentic/<version>/<method>/*.yaml
      match_graphs/<version>/<method>/*.yaml

Key design choices (minimal + robust):
  - Run a linter gate before computing metrics (can be disabled with --no-lint).
  - Derive strict/loose unmatched sets from edges (do not trust YAML lists).
  - Compute "pre-rebuttal severity calibration" directly from severity levels
    (ignore match_graph.severity_alignment labels).
  - Compute decision-driver (positive factor) recall against official pro_accept drivers,
    not against the number of rows in positive_factor_matches.
  - Restore full analytical depth: error-type stratification, issue-type stratification,
    tag analysis, judgment inversions, most-missed concerns, phantom concerns, summary stats.
  - Optional diagnostics:
      * Cluster-level strict recall (to reduce brittleness from over-atomization + 2-edge cap).
      * Phantom subtyping (policy/process vs paper issues) using agentic severity.mechanism.
      * Lightweight groundedness check for phantom concerns with explicit numeric claims.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

try:
    from pypdf import PdfReader  # optional: used only for phantom groundedness diagnostic
except Exception:
    PdfReader = None  # type: ignore


# ============================================================
# Helpers: repo layout detection
# ============================================================

def _exists_dir(p: Path) -> bool:
    return p.exists() and p.is_dir()


def _has_artifact_dirs(base: Path) -> bool:
    """Check if base has the three required artifact subdirectories."""
    official = _exists_dir(base / "official") or _exists_dir(base / "official_concerns")
    agentic = _exists_dir(base / "agentic") or _exists_dir(base / "agentic_concerns")
    return official and agentic and _exists_dir(base / "match_graphs")


def _resolve_artifact_dir(base: Path, canonical: str, alt: str) -> Path:
    """Return the actual directory path, preferring canonical name."""
    if _exists_dir(base / canonical):
        return base / canonical
    return base / alt


def detect_artifact_root(root: Path) -> Path:
    """
    Return the directory that contains {official/, agentic/, match_graphs/}.

    Also accepts the alternate naming {official_concerns/, agentic_concerns/}.
    Searches root itself, root/calibration/concern_alignment, and immediate
    subdirectories.
    """
    root = root.resolve()
    for cand in [root, root / "calibration" / "concern_alignment"]:
        if _has_artifact_dirs(cand):
            return cand
    for sub in (root.iterdir() if root.exists() else []):
        if sub.is_dir() and _has_artifact_dirs(sub):
            return sub
    raise FileNotFoundError(
        f"Could not find artifact dirs under {root}. Expected either:\n"
        f"  {root}/official (or official_concerns), {root}/agentic (or agentic_concerns), {root}/match_graphs\n"
        f"or a subdirectory containing them.\n"
    )


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============================================================
# Optional: paper text loading (for phantom groundedness diagnostic)
# ============================================================

def extract_pdf_text(path: Path, max_pages: Optional[int] = None) -> str:
    """Best-effort PDF text extraction (used only for diagnostics)."""
    if PdfReader is None:
        return ""
    try:
        reader = PdfReader(str(path))
    except Exception:
        return ""
    texts: List[str] = []
    n = len(reader.pages)
    if max_pages is not None:
        n = min(n, max_pages)
    for i in range(n):
        try:
            t = reader.pages[i].extract_text() or ""
        except Exception:
            t = ""
        texts.append(t)
    return "\n".join(texts)


# ============================================================
# Severity comparison utilities
# ============================================================

SEVERITY_ORDER = ["minor", "moderate", "major", "fatal"]
SEV_TO_INT = {s: i for i, s in enumerate(SEVERITY_ORDER)}


def compare_pre_severity(official_sev: Optional[str], agentic_sev: Optional[str]) -> Optional[str]:
    """
    Compute pre-rebuttal severity calibration category for an exact/partial match edge.

    Rules:
      - fatal requires fatal
      - Otherwise: match if |diff| <= 1, under if diff < -1, over if diff > 1
    Returns: 'match' | 'under' | 'over' | None (if missing/unknown).
    """
    if not official_sev or not agentic_sev:
        return None
    o = official_sev.strip().lower()
    a = agentic_sev.strip().lower()
    if o == "unknown" or a == "unknown":
        return None
    if o not in SEV_TO_INT or a not in SEV_TO_INT:
        return None
    if o == "fatal" and a != "fatal":
        return "under"
    if a == "fatal" and o != "fatal":
        return "over"
    diff = SEV_TO_INT[a] - SEV_TO_INT[o]
    if abs(diff) <= 1:
        return "match"
    return "over" if diff > 1 else "under"


# ============================================================
# Core helpers
# ============================================================

def normalize_official_verdict(v: str) -> str:
    v = (v or "").strip().lower()
    if v in {"accepted", "accept"}:
        return "accepted"
    if v in {"rejected", "reject"}:
        return "rejected"
    return v or "unknown"


def normalize_agentic_verdict(v: str) -> str:
    v = (v or "").strip().upper()
    if v in {"ACCEPT", "REJECT"}:
        return v
    return v or "UNKNOWN"


def error_type(official_v: str, agentic_v: str) -> str:
    truth = normalize_official_verdict(official_v)
    pred = normalize_agentic_verdict(agentic_v)
    if truth == "accepted" and pred == "ACCEPT":
        return "TP"
    if truth == "accepted" and pred == "REJECT":
        return "FN"
    if truth == "rejected" and pred == "REJECT":
        return "TN"
    if truth == "rejected" and pred == "ACCEPT":
        return "FP"
    return "NA"


def derive_unmatched_sets(
    official_ids: Set[str],
    agentic_ids: Set[str],
    matches: List[Dict[str, Any]],
) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
    """
    Returns:
      unmatched_official_strict, unmatched_official_loose,
      unmatched_agentic_strict, unmatched_agentic_loose

    strict = no exact/partial edge
    loose  = no edge of any type (exact/partial/related)
    """
    strict_matched_off: Set[str] = set()
    loose_matched_off: Set[str] = set()
    strict_matched_agen: Set[str] = set()
    loose_matched_agen: Set[str] = set()

    for m in matches:
        oid = m.get("official_id")
        aid = m.get("agentic_id")
        mtype = m.get("match_type")
        if oid:
            loose_matched_off.add(oid)
        if aid:
            loose_matched_agen.add(aid)
        if mtype in ("exact", "partial"):
            if oid:
                strict_matched_off.add(oid)
            if aid:
                strict_matched_agen.add(aid)

    return (
        official_ids - strict_matched_off,
        official_ids - loose_matched_off,
        agentic_ids - strict_matched_agen,
        agentic_ids - loose_matched_agen,
    )


# ============================================================
# Cluster scoring utilities (diagnostic)
# ============================================================

# A small, stable stoplist of "generic" tags that are too broad for clustering
# (they tend to connect unrelated concerns into one giant cluster).
GENERIC_CLUSTER_TAGS: Set[str] = {
    "construct_validity",
    "experimental_scope",
    "scope_definition",
    "evaluation_scope",
    "experimental_design",
    "clarity",
    "presentation",
    "readability",
    "formatting",
    "figure_quality",
    "reproducibility",
    "reporting",
}


def build_clusters_from_tags(
    official_concerns: List[Dict[str, Any]],
    freq_threshold: int = 6,
) -> List[List[str]]:
    """
    Deterministically cluster official concerns using tags, intended as a *diagnostic*
    to reduce brittleness from over-atomization and 2-edge cap.

    Clustering rule:
      - Compute tag frequency within the paper.
      - Exclude tags in GENERIC_CLUSTER_TAGS.
      - Additionally exclude tags appearing >= freq_threshold times within the paper.
      - Connect two concerns if they share ANY remaining tag.
      - Clusters are connected components (union-find).

    Returns a sorted list of clusters (each cluster is a sorted list of concern IDs).
    Degenerates to singletons if all tags are excluded or absent.
    """
    ids = [c.get("id") for c in official_concerns if isinstance(c, dict) and c.get("id")]
    ids = [i for i in ids if isinstance(i, str)]
    if not ids:
        return []

    tag_freq: Counter = Counter()
    tags_by_id: Dict[str, Set[str]] = {}
    for c in official_concerns:
        cid = c.get("id")
        if not cid:
            continue
        tags = c.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        tags_set = {t for t in tags if isinstance(t, str)}
        tags_by_id[cid] = tags_set
        for t in tags_set:
            tag_freq[t] += 1

    generic_tags = set(GENERIC_CLUSTER_TAGS)
    if freq_threshold and freq_threshold > 0:
        generic_tags |= {t for t, f in tag_freq.items() if f >= freq_threshold}

    # Union-find with path compression
    parent: Dict[str, str] = {i: i for i in ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            ta = {t for t in tags_by_id.get(a, set()) if t not in generic_tags}
            tb = {t for t in tags_by_id.get(b, set()) if t not in generic_tags}
            if ta and tb and (ta & tb):
                union(a, b)

    clusters: Dict[str, List[str]] = defaultdict(list)
    for i in ids:
        clusters[find(i)].append(i)

    cluster_list = [sorted(v) for v in clusters.values()]
    cluster_list.sort(key=lambda cl: (len(cl), cl[0] if cl else ""))
    return cluster_list


# ============================================================
# Phantom groundedness helpers (diagnostic)
# ============================================================

NUM_RE = re.compile(r"(?<!\w)(\d+(?:\.\d+)?)%?(?!\w)")


def numbers_in_text(s: str) -> Set[str]:
    if not s:
        return set()
    return set(NUM_RE.findall(s))


def get_official_positive_driver_ids(official: Dict[str, Any]) -> Tuple[Set[str], Set[str]]:
    """Returns: (all_pro_accept_driver_ids, pro_accept_pre_driver_ids)."""
    all_ids: Set[str] = set()
    pre_ids: Set[str] = set()
    for d in (official.get("ac_decision_drivers") or []):
        if not isinstance(d, dict) or d.get("polarity") != "pro_accept":
            continue
        did = d.get("id")
        if not did:
            continue
        all_ids.add(did)
        stage = (d.get("observable_stage") or "").strip().lower()
        if stage == "pre_rebuttal":
            pre_ids.add(did)
    return all_ids, pre_ids


def compute_pos_driver_recall(
    official: Dict[str, Any],
    match_graph: Dict[str, Any],
) -> Tuple[Optional[float], Optional[float]]:
    """Recall over official pro_accept decision drivers."""
    official_v = normalize_official_verdict(official.get("official_verdict", ""))
    if official_v != "accepted":
        return None, None
    pro_accept_ids, pro_accept_pre_ids = get_official_positive_driver_ids(official)
    if not pro_accept_ids:
        return None, None
    hits: Set[str] = set()
    hits_pre: Set[str] = set()
    for pm in (match_graph.get("positive_factor_matches") or []):
        if not isinstance(pm, dict):
            continue
        fid = pm.get("official_factor_id")
        if fid not in pro_accept_ids:
            continue
        mtype = pm.get("match_type")
        if mtype and mtype != "none":
            hits.add(fid)
            if fid in pro_accept_pre_ids:
                hits_pre.add(fid)
    recall_all = len(hits) / len(pro_accept_ids) if pro_accept_ids else None
    recall_pre = (len(hits_pre) / len(pro_accept_pre_ids)) if pro_accept_pre_ids else None
    return recall_all, recall_pre


# ============================================================
# Per-paper-method analysis
# ============================================================


# ============================================================
# Rebuttal-aware concern stratification
# ============================================================

# Stratum definitions per v2 plan §3
REBUTTAL_STRATA = {
    "decisive_blocker": {"decisive_blocker"},
    "unresolved": {"unresolved"},
    "accepted_limitation": {"accepted_limitation"},
    "resolved": {"resolved", "dismissed", "reframed_feature"},
    "ambiguous": {"not_mentioned"},
}

# Denominator tiers (v2 plan §3):
#   (a) all: everything
#   (b) non_resolved: all minus resolved+dismissed+reframed_feature
#   (c) still_standing: decisive_blocker + unresolved + accepted_limitation
TIER_B_EXCLUDE = {"resolved", "dismissed", "reframed_feature"}
TIER_C_INCLUDE = {"decisive_blocker", "unresolved", "accepted_limitation"}


def stratify_official_concerns(
    off_concerns: Dict[str, Dict],
    rebuttal_aware: bool = False,
) -> Dict[str, Any]:
    """Stratify official concerns by ac_treatment and compute denominator tiers.

    Returns dict with:
      strata: {stratum_name: set of concern IDs}
      tier_a_ids: all concern IDs (full denominator)
      tier_b_ids: non-resolved concern IDs
      tier_c_ids: still-standing concern IDs
      addressed_in_pdf_ids: concerns resolved AND fixed in the PDF the system reviewed
    """
    all_ids = set(off_concerns.keys())
    result = {
        "strata": defaultdict(set),
        "tier_a_ids": all_ids,
        "tier_b_ids": set(all_ids),
        "tier_c_ids": set(),
        "addressed_in_pdf_ids": set(),
    }

    if not rebuttal_aware:
        # Without rebuttal awareness, all tiers are the same
        result["tier_b_ids"] = set(all_ids)
        result["tier_c_ids"] = set(all_ids)
        return result

    for cid, c in off_concerns.items():
        ac = (c.get("ac_treatment") or "not_mentioned").strip().lower()

        # Assign to stratum
        assigned = False
        for stratum, values in REBUTTAL_STRATA.items():
            if ac in values:
                result["strata"][stratum].add(cid)
                assigned = True
                break
        if not assigned:
            result["strata"]["ambiguous"].add(cid)

        # Tier B: exclude resolved
        if ac in TIER_B_EXCLUDE:
            # Check addressed_in_pdf: if concern was resolved AND the fix is
            # in the PDF the system reviewed, exclude from ALL tiers
            if c.get("addressed_in_pdf", True):
                result["addressed_in_pdf_ids"].add(cid)
            result["tier_b_ids"].discard(cid)

        # Tier C: only still-standing
        if ac in TIER_C_INCLUDE:
            result["tier_c_ids"].add(cid)

    # Remove addressed_in_pdf concerns from all tiers
    for tier_key in ("tier_a_ids", "tier_b_ids", "tier_c_ids"):
        result[tier_key] -= result["addressed_in_pdf_ids"]

    return result


def _agen_severity_sort_key(concern: Dict[str, Any]) -> Tuple[int, str]:
    """Sort key for agentic concerns: highest severity first, then by ID for stability."""
    sev = concern.get("severity")
    if isinstance(sev, dict):
        level = sev.get("level", "minor")
    elif isinstance(sev, str):
        level = sev
    else:
        level = "minor"
    # Negate so fatal (3) sorts first
    return (-SEV_TO_INT.get(level.strip().lower(), 0), concern.get("id", ""))


def analyze_paper_method(
    paper: str,
    method: str,
    official: Dict[str, Any],
    agentic: Dict[str, Any],
    match_graph: Dict[str, Any],
    paper_text: Optional[str] = None,
    cluster_generic_threshold: int = 6,
    exclude_artifacts: bool = False,
    rebuttal_aware: bool = False,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """Analyze a single match graph to extract all metrics."""
    off_concerns = {c["id"]: c for c in (official.get("concerns") or []) if isinstance(c, dict) and "id" in c}
    agen_concerns = {c["id"]: c for c in (agentic.get("concerns") or []) if isinstance(c, dict) and "id" in c}

    # --exclude-artifacts: remove policy artifacts from agentic concerns
    artifact_ids: Set[str] = set()
    artifact_missing_field = 0
    if exclude_artifacts:
        for cid, c in list(agen_concerns.items()):
            if "is_policy_artifact" not in c:
                artifact_missing_field += 1
            if c.get("is_policy_artifact", False):
                artifact_ids.add(cid)
        for cid in artifact_ids:
            del agen_concerns[cid]
        if artifact_missing_field > 0:
            import logging
            logging.getLogger(__name__).warning(
                "%s: %d/%d agentic concerns missing is_policy_artifact field",
                paper, artifact_missing_field,
                artifact_missing_field + len(agen_concerns) + len(artifact_ids),
            )

    # --top-k: keep only the k most severe agentic concerns per paper.
    # Ensures all methods are compared at equal depth, controlling for
    # atomization differences between systems that split one concern into
    # several vs systems that fold several into one.
    topk_dropped_ids: Set[str] = set()
    if top_k is not None and len(agen_concerns) > top_k:
        sorted_concerns = sorted(agen_concerns.values(), key=_agen_severity_sort_key)
        keep_ids = {c["id"] for c in sorted_concerns[:top_k]}
        topk_dropped_ids = set(agen_concerns.keys()) - keep_ids
        agen_concerns = {cid: c for cid, c in agen_concerns.items() if cid in keep_ids}

    # Rebuttal-aware stratification of official concerns
    strat = stratify_official_concerns(off_concerns, rebuttal_aware=rebuttal_aware)

    official_ids = set(off_concerns.keys())
    agentic_ids = set(agen_concerns.keys())
    raw_matches = match_graph.get("matches") or []

    # Filter match edges involving excluded agentic concerns (artifacts + top-k dropped)
    excluded_agen_ids = artifact_ids | topk_dropped_ids
    matches = [
        m for m in raw_matches
        if m.get("agentic_id") not in excluded_agen_ids
    ]
    sole_match_artifacts = 0  # Official concerns whose ONLY match was an excluded concern
    if excluded_agen_ids:
        off_matched_before = {m.get("official_id") for m in raw_matches if m.get("official_id")}
        off_matched_after = {m.get("official_id") for m in matches if m.get("official_id")}
        sole_match_artifacts = len(off_matched_before - off_matched_after)

    # Derived unmatched sets
    unmatched_off_strict, unmatched_off_loose, unmatched_agen_strict, unmatched_agen_loose = derive_unmatched_sets(
        official_ids, agentic_ids, matches
    )

    # -- Tier (a): all official concerns (backward-compatible denominator) --
    total_official = len(official_ids)
    total_agentic = len(agentic_ids)

    strict_matched_official = total_official - len(unmatched_off_strict)
    loose_matched_official = total_official - len(unmatched_off_loose)
    strict_matched_agentic = total_agentic - len(unmatched_agen_strict)

    issue_recall_strict = strict_matched_official / total_official if total_official else 0.0
    issue_recall_loose = loose_matched_official / total_official if total_official else 0.0
    issue_precision = strict_matched_agentic / total_agentic if total_agentic else 0.0
    phantom_rate_strict = len(unmatched_agen_strict) / total_agentic if total_agentic else 0.0
    phantom_rate_loose = len(unmatched_agen_loose) / total_agentic if total_agentic else 0.0

    # -- Rebuttal-aware tiered recall --
    strict_matched_off_ids = official_ids - unmatched_off_strict
    loose_matched_off_ids = official_ids - unmatched_off_loose

    def _tier_recall(tier_ids: Set[str], matched_ids: Set[str]) -> Optional[float]:
        if not tier_ids:
            return None
        return len(tier_ids & matched_ids) / len(tier_ids)

    # Tier (b): non-resolved denominator
    recall_strict_tier_b = _tier_recall(strat["tier_b_ids"], strict_matched_off_ids)
    recall_loose_tier_b = _tier_recall(strat["tier_b_ids"], loose_matched_off_ids)
    # Tier (c): still-standing denominator
    recall_strict_tier_c = _tier_recall(strat["tier_c_ids"], strict_matched_off_ids)
    recall_loose_tier_c = _tier_recall(strat["tier_c_ids"], loose_matched_off_ids)

    # Per-stratum recall (strict)
    stratum_recall: Dict[str, Optional[float]] = {}
    for stratum_name, stratum_ids in strat["strata"].items():
        stratum_recall[stratum_name] = _tier_recall(stratum_ids, strict_matched_off_ids)

    # Match type counts
    match_types = Counter()
    judgment_types = Counter()
    severity_types = Counter()

    # Rich edge data for stratification
    match_edges = []
    for m in matches:
        oid = m.get("official_id")
        aid = m.get("agentic_id")
        mtype = m.get("match_type", "unknown")
        jalign = m.get("judgment_alignment", "n/a")
        salign = m.get("severity_alignment", "n/a")

        match_types[mtype] += 1
        judgment_types[jalign] += 1
        severity_types[salign] += 1

        off_concern = off_concerns.get(oid)
        match_edges.append({
            "official_id": oid,
            "agentic_id": aid,
            "match_type": mtype,
            "judgment_alignment": jalign,
            "severity_alignment": salign,
            "official_severity": off_concern.get("severity") if off_concern else None,
            "official_decisive": off_concern.get("decisive", False) if off_concern else False,
            "official_issue_type": off_concern.get("issue_type") if off_concern else None,
            "official_tags": off_concern.get("tags", []) if off_concern else [],
            "official_ac_treatment": off_concern.get("ac_treatment") if off_concern else None,
        })

    # Judgment inversion rate over strict edges
    strict_edges = [m for m in matches if m.get("match_type") in ("exact", "partial")]
    inv = sum(1 for m in strict_edges if m.get("judgment_alignment") == "inverted")
    inversion_rate = inv / len(strict_edges) if strict_edges else None

    # Pre-severity calibration counts over strict edges
    sev_pre_counts: Counter = Counter()
    for m in strict_edges:
        oid = m.get("official_id")
        aid = m.get("agentic_id")
        off = off_concerns.get(oid or "")
        agen = agen_concerns.get(aid or "")
        if not off or not agen:
            continue
        off_sev = off.get("severity")
        agen_sev = (agen.get("severity") or {}).get("level") if isinstance(agen.get("severity"), dict) else None
        cat = compare_pre_severity(off_sev, agen_sev)
        if cat:
            sev_pre_counts[cat] += 1

    total_sev = sum(sev_pre_counts.values())
    sev_pre_under_rate = (sev_pre_counts.get("under", 0) / total_sev) if total_sev else None
    sev_pre_over_rate = (sev_pre_counts.get("over", 0) / total_sev) if total_sev else None

    # Severity rates from YAML labels (for backward compatibility)
    total_sev_labeled = sum(v for k, v in severity_types.items() if k != "n/a")
    under_rate = severity_types.get("under", 0) / total_sev_labeled if total_sev_labeled else 0
    over_rate = severity_types.get("over", 0) / total_sev_labeled if total_sev_labeled else 0

    # Decisive recall
    decisive_ids = {cid for cid, c in off_concerns.items() if c.get("decisive", False)}
    decisive_total = len(decisive_ids)
    decisive_matched = len(decisive_ids - unmatched_off_strict)
    decisive_recall = decisive_matched / decisive_total if decisive_total else None

    # Positive factor recall
    pos_recall_all, pos_recall_pre = compute_pos_driver_recall(official, match_graph)

    # Diagnostic: cluster recall (strict) from official tags
    clusters = build_clusters_from_tags(list(off_concerns.values()), freq_threshold=cluster_generic_threshold)
    cluster_total = len(clusters)
    strict_matched_off_ids = official_ids - unmatched_off_strict
    cluster_hit = 0
    for cl in clusters:
        if any(oid in strict_matched_off_ids for oid in cl):
            cluster_hit += 1
    cluster_recall_strict = (cluster_hit / cluster_total) if cluster_total else None

    # Diagnostic: phantom policy/process count via severity.mechanism
    phantom_policy_count = 0
    for aid in unmatched_agen_strict:
        agen = agen_concerns.get(aid)
        mech = None
        if agen and isinstance(agen.get("severity"), dict):
            mech = agen["severity"].get("mechanism")
        mech_norm = (mech or "none").strip().lower()
        if mech_norm and mech_norm != "none":
            phantom_policy_count += 1
    phantom_policy_rate = (phantom_policy_count / total_agentic) if total_agentic else None

    # Diagnostic: phantom numeric groundedness (lower bound)
    # IMPORTANT: When paper_text is None/empty, we cannot assess groundedness.
    # Report n/a (not 0%) to avoid the "phantom numeric groundedness" measurement
    # artifact where 0% groundedness simply means "no paper text was loaded."
    has_paper_text = bool(paper_text)
    phantom_num_total = 0
    phantom_num_grounded = 0
    for aid in unmatched_agen_strict:
        agen = agen_concerns.get(aid)
        if not agen:
            continue
        nums = numbers_in_text(agen.get("text") or "")
        if not nums:
            continue
        phantom_num_total += 1
        if has_paper_text:
            if any(n in paper_text for n in nums):
                phantom_num_grounded += 1

    # Phantom rate from YAML (for legacy sections)
    yaml_unmatched_agen = match_graph.get("unmatched_agentic", []) or []
    yaml_unmatched_off = match_graph.get("unmatched_official", []) or []

    # Verdict info
    off_verdict = normalize_official_verdict(official.get("official_verdict"))
    agen_verdict = normalize_agentic_verdict(agentic.get("verdict"))
    et = error_type(official.get("official_verdict"), agentic.get("verdict"))

    return {
        "paper": paper,
        "method": method,
        "official_verdict": off_verdict,
        "agentic_verdict": agen_verdict,
        "error_type": et,
        "total_official": total_official,
        "total_agentic": total_agentic,
        "issue_recall_strict": issue_recall_strict,
        "issue_recall_loose": issue_recall_loose,
        "issue_precision": issue_precision,
        "phantom_rate_strict": phantom_rate_strict,
        "phantom_rate_loose": phantom_rate_loose,
        "inversion_rate": inversion_rate if inversion_rate is not None else 0,
        "under_rate": under_rate,
        "over_rate": over_rate,
        "match_types": dict(match_types),
        "judgment_types": dict(judgment_types),
        "severity_types": dict(severity_types),
        "match_edges": match_edges,
        "decisive_total": decisive_total,
        "decisive_matched": decisive_matched,
        "decisive_recall": decisive_recall,
        "pos_recall_all": pos_recall_all,
        "pos_recall_pre": pos_recall_pre,
        "sev_pre_counts": sev_pre_counts,
        "sev_pre_under_rate": sev_pre_under_rate,
        "sev_pre_over_rate": sev_pre_over_rate,
        "yaml_unmatched_official": yaml_unmatched_off,
        "yaml_unmatched_agentic": yaml_unmatched_agen,
        "unmatched_off_strict": unmatched_off_strict,
        "unmatched_agen_strict": unmatched_agen_strict,
        # New diagnostics
        "cluster_total": cluster_total,
        "cluster_hit_strict": cluster_hit,
        "cluster_recall_strict": cluster_recall_strict,
        "phantom_policy_count": phantom_policy_count,
        "phantom_policy_rate": phantom_policy_rate,
        "phantom_num_total": phantom_num_total,
        "phantom_num_grounded": phantom_num_grounded,
        "has_paper_text": has_paper_text,
        "phantom_num_grounded_rate": (
            (phantom_num_grounded / phantom_num_total)
            if phantom_num_total and has_paper_text
            else None
        ),
        # v2: artifact filtering stats + top-k
        "artifact_count": len(artifact_ids),
        "topk_dropped": len(topk_dropped_ids),
        "artifact_missing_field": artifact_missing_field,
        "sole_match_artifacts": sole_match_artifacts,
        # v2: rebuttal-aware tiered recall
        "tier_a_size": len(strat["tier_a_ids"]),
        "tier_b_size": len(strat["tier_b_ids"]),
        "tier_c_size": len(strat["tier_c_ids"]),
        "addressed_in_pdf_count": len(strat["addressed_in_pdf_ids"]),
        "recall_strict_tier_b": recall_strict_tier_b,
        "recall_loose_tier_b": recall_loose_tier_b,
        "recall_strict_tier_c": recall_strict_tier_c,
        "recall_loose_tier_c": recall_loose_tier_c,
        "stratum_recall": stratum_recall,
    }


# ============================================================
# Display helpers
# ============================================================

def fmt(val, pct=True):
    if val is None:
        return "n/a"
    if pct:
        return f"{val * 100:.1f}%"
    return f"{val:.2f}"


def print_section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def mean(values):
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def print_table(rows, headers):
    col_widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    fmt_str = "  ".join("{:<" + str(w) + "}" for w in col_widths)
    print(fmt_str.format(*headers))
    print("-" * (sum(col_widths) + 2 * (len(col_widths) - 1)))
    for r in rows:
        print(fmt_str.format(*r))


# ============================================================
# Linter gate
# ============================================================

def run_linter(artifact_root: Path, version: str, strict: bool = False) -> None:
    lint_path = Path(__file__).resolve().parent / "lint_concern_alignment.py"
    if not lint_path.exists():
        return
    cmd = [sys.executable, str(lint_path), "--root", str(artifact_root), "--version", version]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        if strict:
            sys.stderr.write(proc.stdout)
            sys.stderr.write(proc.stderr)
            raise SystemExit(proc.returncode)
        else:
            print("Lint warnings (use --strict-lint to make these fatal):")
            sys.stdout.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)


# ============================================================
# Semantic override support (Skill 5)
# ============================================================

def load_overrides(paths: List[str]) -> Dict[str, Any]:
    """Load and merge one or more semantic override YAML files.

    Returns a dict with:
      edge_overrides: keyed by (method, paper, official_id, agentic_id)
      phantom_judgments: keyed by (method, paper, agentic_id)
    """
    edge_idx: Dict[tuple, Dict[str, Any]] = {}
    phantom_idx: Dict[tuple, Dict[str, Any]] = {}
    warnings_found = 0
    for p in paths:
        data = load_yaml(Path(p))
        for eo in (data.get("edge_overrides") or []):
            key = (eo["method"], eo["paper"], eo["official_id"], eo["agentic_id"])
            edge_idx[key] = eo
            # QA: verdict/action consistency
            verdict = eo.get("verdict", "correct")
            action = eo.get("action", "confirmed")
            edge_label = f"{eo['method']}/{eo['paper']} {eo['official_id']}/{eo['agentic_id']}"
            if verdict == "correct" and action != "confirmed":
                print(f"  [QA WARNING] {edge_label}: verdict=correct but action={action}", file=sys.stderr)
                warnings_found += 1
            if action == "confirmed" and verdict != "correct":
                print(f"  [QA WARNING] {edge_label}: action=confirmed but verdict={verdict}", file=sys.stderr)
                warnings_found += 1
            if action == "removed" and verdict != "wrong_match":
                print(f"  [QA WARNING] {edge_label}: action=removed but verdict={verdict}", file=sys.stderr)
                warnings_found += 1
            if action == "reclassified" and verdict not in ("wrong_type", "wrong_severity", "multiple_errors"):
                print(f"  [QA WARNING] {edge_label}: action=reclassified but verdict={verdict}", file=sys.stderr)
                warnings_found += 1
            # QA: labels must differ from original when verdict != correct
            if verdict == "correct":
                orig_mt = eo.get("original_match_type")
                override_mt = eo.get("override_match_type")
                override_sa = eo.get("override_severity_alignment")
                if orig_mt and override_mt and orig_mt != override_mt:
                    print(f"  [QA WARNING] {edge_label}: verdict=correct but match_type changed "
                          f"{orig_mt}->{override_mt}", file=sys.stderr)
                    warnings_found += 1
        for pj in (data.get("phantom_judgments") or []):
            key = (pj["method"], pj["paper"], pj["agentic_id"])
            phantom_idx[key] = pj
    if warnings_found:
        print(f"  [QA] {warnings_found} override consistency warnings found. "
              f"Run fix_severity_alignment.py --fix-override-verdicts to fix.", file=sys.stderr)
    return {"edge_overrides": edge_idx, "phantom_judgments": phantom_idx}


def apply_overrides(
    match_graph: Dict[str, Any],
    overrides: Dict[str, Any],
    paper: str,
    method: str,
) -> Dict[str, Any]:
    """Apply semantic overrides to a match graph before metric computation.

    Actions:
      - confirmed: no-op (original labels kept)
      - reclassified: update match_type, judgment_alignment, severity_alignment
      - removed: delete edge from matches list

    Returns: (possibly modified) match_graph dict and a stats dict.
    """
    edge_idx = overrides["edge_overrides"]
    matches = match_graph.get("matches") or []
    new_matches = []
    stats = {"confirmed": 0, "reclassified": 0, "removed": 0}

    for edge in matches:
        key = (method, paper, edge.get("official_id"), edge.get("agentic_id"))
        ov = edge_idx.get(key)
        if ov is None:
            new_matches.append(edge)
            continue
        action = ov.get("action", "confirmed")
        if action == "confirmed":
            stats["confirmed"] += 1
            new_matches.append(edge)
        elif action == "reclassified":
            stats["reclassified"] += 1
            edge = dict(edge)  # shallow copy to avoid mutating original
            edge["match_type"] = ov["override_match_type"]
            edge["judgment_alignment"] = ov["override_judgment_alignment"]
            edge["severity_alignment"] = ov["override_severity_alignment"]
            new_matches.append(edge)
        elif action == "removed":
            stats["removed"] += 1
            # Edge is dropped — not added to new_matches
        else:
            new_matches.append(edge)

    match_graph = dict(match_graph)
    match_graph["matches"] = new_matches
    return match_graph, stats


# ============================================================
# Human judgment support
# ============================================================

def load_human_judgments(judgments_dir: Path) -> Dict[str, Any]:
    """Load human judgment files from a directory.

    Expects:
      - severity_triage.yaml (human verdicts on severity-misaligned edges)
      - concern_triage.yaml (human categorization of misses and phantoms)

    Returns dict with loaded data (or empty structures if files not found).
    """
    result: Dict[str, Any] = {
        "severity_triage": None,
        "concern_triage": None,
    }

    # Check both naming conventions: _queue.yaml (from generate_triage_queue.py)
    # and plain .yaml (for hand-created files)
    for sev_name in ("severity_triage_queue.yaml", "severity_triage.yaml"):
        sev_path = judgments_dir / sev_name
        if sev_path.exists():
            result["severity_triage"] = load_yaml(sev_path)
            break

    for concern_name in ("concern_triage_queue.yaml", "concern_triage.yaml"):
        concern_path = judgments_dir / concern_name
        if concern_path.exists():
            result["concern_triage"] = load_yaml(concern_path)
            break

    return result


def compute_human_calibrated_metrics(
    human_judgments: Dict[str, Any],
    all_results: Dict[tuple, Dict[str, Any]],
    methods: List[str],
    papers: List[str],
) -> None:
    """Compute and print human-calibrated metrics from judgment files."""
    print_section("HUMAN-CALIBRATED METRICS")

    severity_data = human_judgments.get("severity_triage")
    concern_data = human_judgments.get("concern_triage")

    has_severity = severity_data is not None and severity_data.get("judgments")
    has_concerns = concern_data is not None and (
        concern_data.get("misses") or concern_data.get("phantoms")
    )

    if not has_severity and not has_concerns:
        print("  No completed human judgments found.")
        return

    # ---- Severity triage analysis ----
    if has_severity:
        judgments = severity_data["judgments"]
        # Filter out TODO entries
        completed = [j for j in judgments if j.get("human_verdict") not in ("TODO", None, "")]
        total_judged = len(completed)

        print(f"\n  Severity triage: {total_judged} edges judged (of {len(judgments)} queued)")

        if completed:
            verdict_counts: Counter = Counter(j["human_verdict"] for j in completed)
            print(f"    system_correct:    {verdict_counts.get('system_correct', 0)}")
            print(f"    officials_correct: {verdict_counts.get('officials_correct', 0)}")
            print(f"    context_dependent: {verdict_counts.get('context_dependent', 0)}")

            # Adjusted severity accuracy:
            # Standard: count of severity-aligned edges / total edges
            # Adjusted: edges where system was correct (system_correct) are NOT miscalibrated
            # So adjusted = (aligned_edges + system_correct) / total_edges
            system_correct_count = verdict_counts.get("system_correct", 0)
            officials_correct_count = verdict_counts.get("officials_correct", 0)
            context_dependent_count = verdict_counts.get("context_dependent", 0)

            # Compute total severity edges across all results (edges with severity != n/a)
            total_sev_edges = 0
            misaligned_sev_edges = 0
            for d in all_results.values():
                for k, v in d["severity_types"].items():
                    if k != "n/a":
                        total_sev_edges += v
                    if k in ("under", "over"):
                        misaligned_sev_edges += v

            aligned_sev_edges = total_sev_edges - misaligned_sev_edges
            if total_sev_edges > 0:
                standard_accuracy = aligned_sev_edges / total_sev_edges
                # Adjusted: system_correct edges are no longer miscalibrated
                adjusted_aligned = aligned_sev_edges + system_correct_count
                # context_dependent gets half credit
                adjusted_aligned += context_dependent_count * 0.5
                adjusted_accuracy = adjusted_aligned / total_sev_edges

                print(f"\n    Standard severity accuracy:  {standard_accuracy:.1%} "
                      f"({aligned_sev_edges}/{total_sev_edges})")
                print(f"    Adjusted severity accuracy:  {adjusted_accuracy:.1%} "
                      f"({adjusted_aligned:.0f}/{total_sev_edges})")
                print(f"      (+{system_correct_count} system_correct, "
                      f"+{context_dependent_count * 0.5:.0f} context_dependent*0.5)")

            # Action distribution
            action_counts: Counter = Counter(j.get("action", "no_action") for j in completed)
            if any(a != "no_action" for a in action_counts):
                print("\n    Action recommendations:")
                for action in ["dampening_candidate", "escalation_candidate",
                              "rule_change_candidate", "example_candidate", "no_action"]:
                    count = action_counts.get(action, 0)
                    if count:
                        print(f"      {action}: {count}")

            # Breakdown by severity alignment type
            by_sa: Dict[str, Counter] = defaultdict(Counter)
            for j in completed:
                sa = j.get("severity_alignment", "unknown")
                by_sa[sa][j["human_verdict"]] += 1

            if len(by_sa) > 1:
                print("\n    By severity alignment type:")
                for sa in ["inverted", "over", "under"]:
                    if sa in by_sa:
                        counts = by_sa[sa]
                        total = sum(counts.values())
                        sc = counts.get("system_correct", 0)
                        oc = counts.get("officials_correct", 0)
                        cd = counts.get("context_dependent", 0)
                        print(f"      {sa} (n={total}): "
                              f"sys_correct={sc}, off_correct={oc}, ctx_dep={cd}")

    # ---- Concern triage analysis ----
    if has_concerns:
        misses = concern_data.get("misses") or []
        phantoms = concern_data.get("phantoms") or []

        # Filter completed entries
        completed_misses = [m for m in misses if m.get("miss_type") not in ("TODO", None, "")]
        completed_phantoms = [p for p in phantoms if p.get("phantom_type") not in ("TODO", None, "")]

        print(f"\n  Concern triage: {len(completed_misses)} misses judged (of {len(misses)} queued), "
              f"{len(completed_phantoms)} phantoms judged (of {len(phantoms)} queued)")

        if completed_misses:
            miss_type_counts: Counter = Counter(m["miss_type"] for m in completed_misses)
            print(f"\n    Miss categorization:")
            print(f"      structural_gap:    {miss_type_counts.get('structural_gap', 0)}")
            print(f"      detection_failure: {miss_type_counts.get('detection_failure', 0)}")
            print(f"      unobservable:      {miss_type_counts.get('unobservable', 0)}")

            # Actionable misses (structural_gap + detection_failure)
            actionable = (miss_type_counts.get("structural_gap", 0) +
                         miss_type_counts.get("detection_failure", 0))
            total_m = sum(miss_type_counts.values())
            if total_m:
                print(f"      Actionable rate: {actionable}/{total_m} ({actionable/total_m:.1%})")

            # Misses by severity
            miss_sev_counts: Counter = Counter()
            for m in completed_misses:
                sev = m.get("official_severity", "unknown")
                mtype = m["miss_type"]
                miss_sev_counts[(sev, mtype)] += 1

            if miss_sev_counts:
                print("\n    Misses by severity x type:")
                for sev in ["fatal", "major", "moderate", "minor"]:
                    sg = miss_sev_counts.get((sev, "structural_gap"), 0)
                    df = miss_sev_counts.get((sev, "detection_failure"), 0)
                    uo = miss_sev_counts.get((sev, "unobservable"), 0)
                    total_sev = sg + df + uo
                    if total_sev:
                        print(f"      {sev}: struct_gap={sg}, detect_fail={df}, unobs={uo}")

        if completed_phantoms:
            phantom_type_counts: Counter = Counter(p["phantom_type"] for p in completed_phantoms)
            print(f"\n    Phantom categorization:")
            print(f"      valid_concern:   {phantom_type_counts.get('valid_concern', 0)}")
            print(f"      policy_artifact: {phantom_type_counts.get('policy_artifact', 0)}")
            print(f"      hallucination:   {phantom_type_counts.get('hallucination', 0)}")

            # Adjusted phantom rate: valid_concerns are not really phantoms
            valid_count = phantom_type_counts.get("valid_concern", 0)
            total_p = sum(phantom_type_counts.values())
            policy_count = phantom_type_counts.get("policy_artifact", 0)
            halluc_count = phantom_type_counts.get("hallucination", 0)
            true_phantom_count = policy_count + halluc_count

            if total_p:
                print(f"\n      True phantom rate (excl valid_concern): "
                      f"{true_phantom_count}/{total_p} ({true_phantom_count/total_p:.1%})")
                print(f"      Valid concerns missed by officials: "
                      f"{valid_count}/{total_p} ({valid_count/total_p:.1%})")


# ============================================================
# Main
# ============================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, default=".", help="Repo root (or parent containing concern_alignment artifacts).")
    ap.add_argument("--version", type=str, required=True, help="Artifact version folder under agentic/ and match_graphs/ (e.g. 'v1', 'public_slice').")
    ap.add_argument("--no-lint", action="store_true", help="Skip lint gate entirely.")
    ap.add_argument("--strict-lint", action="store_true", help="Treat lint warnings as fatal errors.")
    ap.add_argument(
        "--cluster-generic-threshold",
        type=int,
        default=6,
        help="Within-paper frequency threshold for excluding broad tags in clustering (diagnostic). Default 6.",
    )
    ap.add_argument(
        "--paper-text-max-pages",
        type=int,
        default=None,
        help="If set, only extract this many pages from each paper PDF (diagnostic groundedness only).",
    )
    ap.add_argument(
        "--papers-dir",
        type=str,
        default=None,
        help="Directory containing {paper}.pdf files for groundedness diagnostic. "
             "Defaults to <artifact_root>/papers/ if present.",
    )
    ap.add_argument(
        "--overrides",
        type=str,
        nargs="*",
        default=None,
        help="One or more semantic override YAML files (from Skill 5). "
             "Applied to match graphs before metric computation.",
    )
    ap.add_argument(
        "--human-judgments",
        type=str,
        default=None,
        help="Directory containing human judgment files (severity_triage.yaml and "
             "concern_triage.yaml). When provided, computes human-calibrated metrics "
             "after standard metrics.",
    )
    ap.add_argument(
        "--methods",
        type=str,
        nargs="*",
        default=None,
        help="Restrict to specific method subdirectories (e.g., --methods e1_liang_run1 e1_liang_run2). "
             "By default, discovers all subdirectories under agentic/{version}/.",
    )
    ap.add_argument(
        "--exclude-artifacts",
        action="store_true",
        help="Exclude agentic concerns tagged is_policy_artifact=true from metrics. "
             "Concerns missing the field are included with a warning.",
    )
    ap.add_argument(
        "--rebuttal-aware",
        action="store_true",
        help="Stratify official concerns by ac_treatment and report 3-tier recall: "
             "all / non-resolved / still-standing. Automatically handles addressed_in_pdf.",
    )
    ap.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Cap agentic concerns at k per paper (most severe kept). "
             "Controls for atomization differences across methods. "
             "Concerns are sorted by severity (fatal > major > moderate > minor).",
    )
    ap.add_argument(
        "--export-per-paper",
        type=str,
        default=None,
        metavar="PATH",
        help="Export per-paper metrics as YAML for downstream consumption by "
             "compute_statistical_tests.py. Writes one file per method to PATH/.",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    artifact_root = detect_artifact_root(root)

    official_dir = _resolve_artifact_dir(artifact_root, "official", "official_concerns")
    agentic_base = _resolve_artifact_dir(artifact_root, "agentic", "agentic_concerns")
    # Support both versioned (agentic/{version}/) and flat (agentic/) layouts
    agentic_dir = agentic_base / args.version if (agentic_base / args.version).is_dir() else agentic_base
    match_dir = artifact_root / "match_graphs" / args.version if (artifact_root / "match_graphs" / args.version).is_dir() else artifact_root / "match_graphs"
    papers_dir = Path(args.papers_dir) if args.papers_dir else artifact_root / "papers"

    if not args.no_lint:
        run_linter(artifact_root, args.version, strict=args.strict_lint)

    # Discover papers and methods dynamically
    papers = sorted(p.stem for p in official_dir.glob("*.yaml"))
    if args.methods:
        methods = args.methods
    else:
        methods = sorted(d.name for d in agentic_dir.iterdir() if d.is_dir()) if agentic_dir.is_dir() else []

    if not papers:
        raise SystemExit(f"No official/*.yaml found under {official_dir}")
    if not methods:
        raise SystemExit(f"No agentic/{args.version}/* method dirs found under {agentic_dir}")

    # Pre-load paper text (optional, for phantom groundedness diagnostic)
    paper_text_by_paper: Dict[str, str] = {}
    if papers_dir.exists() and papers_dir.is_dir() and PdfReader is not None:
        for paper in papers:
            pdf_path = papers_dir / f"{paper}.pdf"
            if pdf_path.exists():
                paper_text_by_paper[paper] = extract_pdf_text(pdf_path, max_pages=args.paper_text_max_pages)
        if paper_text_by_paper:
            print(f"Loaded PDF text for {len(paper_text_by_paper)} papers (groundedness diagnostic).")

    # Load semantic overrides (Skill 5)
    all_overrides: Optional[Dict[str, Any]] = None
    override_stats_total: Counter = Counter()
    phantom_judgments_all: List[Dict[str, Any]] = []
    if args.overrides:
        all_overrides = load_overrides(args.overrides)
        n_edges = len(all_overrides["edge_overrides"])
        n_phantoms = len(all_overrides["phantom_judgments"])
        print(f"Loaded semantic overrides: {n_edges} edge overrides, {n_phantoms} phantom judgments")
        phantom_judgments_all = list(all_overrides["phantom_judgments"].values())

    # Load all data
    all_officials = {}
    all_results: Dict[tuple, Dict[str, Any]] = {}

    # v2 pipeline banner
    if args.exclude_artifacts or args.rebuttal_aware or args.top_k:
        flags = []
        if args.exclude_artifacts:
            flags.append("--exclude-artifacts")
        if args.rebuttal_aware:
            flags.append("--rebuttal-aware")
        if args.top_k:
            flags.append(f"--top-k {args.top_k}")
        print(f"\n{'='*60}")
        print(f"  CONCERN ALIGNMENT v2: {' + '.join(flags)}")
        print(f"{'='*60}\n")

    print("Loading official concern sheets...")
    for paper in papers:
        off = load_yaml(official_dir / f"{paper}.yaml")
        all_officials[paper] = off
        n_concerns = len(off.get("concerns", []))
        n_decisive = sum(1 for c in off.get("concerns", []) if c.get("decisive", False))
        print(f"  {paper}: {n_concerns} concerns, {n_decisive} decisive")

    print("\nLoading match graphs and computing per-paper metrics...")
    for method in methods:
        for paper in papers:
            ag_path = agentic_dir / method / f"{paper}.yaml"
            mg_path = match_dir / method / f"{paper}.yaml"
            if not ag_path.exists() or not mg_path.exists():
                continue
            ag = load_yaml(ag_path)
            mg = load_yaml(mg_path)
            if all_overrides is not None:
                mg, ov_stats = apply_overrides(mg, all_overrides, paper, method)
                override_stats_total.update(ov_stats)
            result = analyze_paper_method(
                paper, method, all_officials[paper], ag, mg,
                paper_text=paper_text_by_paper.get(paper),
                cluster_generic_threshold=args.cluster_generic_threshold,
                exclude_artifacts=args.exclude_artifacts,
                rebuttal_aware=args.rebuttal_aware,
                top_k=args.top_k,
            )
            all_results[(method, paper)] = result
            print(f"  {method}/{paper} [{result['error_type']}]: "
                  f"recall={fmt(result['issue_recall_strict'])}, "
                  f"precision={fmt(result['issue_precision'])}, "
                  f"inversions={result['judgment_types'].get('inverted', 0)}")

    # ============================================================
    # 1. Error type matrix
    # ============================================================
    print_section("ERROR TYPE MATRIX")
    headers = ["paper", "truth"] + methods
    rows = []
    for paper in papers:
        truth = normalize_official_verdict(all_officials[paper].get("official_verdict"))
        row = [paper, truth]
        for method in methods:
            entries = all_results.get((method, paper))
            row.append(entries["error_type"] if entries else "NA")
        rows.append(row)
    print_table(rows, headers)

    # ============================================================
    # 2. Per-method aggregates (macro average)
    # ============================================================
    print_section("PER-METHOD AGGREGATE METRICS (macro)")
    agg_headers = [
        "method", "issue_recall_strict", "issue_recall_loose", "issue_precision",
        "phantom_rate", "cluster_rcl", "phant_policy", "phant_grnd",
        "inv_rate",
        "sev_pre_under", "sev_pre_over",
        "decisive_recall", "pos_driver_rcl", "pos_drv_pre",
    ]
    agg_rows = []
    for method in methods:
        items = [(p, all_results[(method, p)]) for p in papers if (method, p) in all_results]
        if not items:
            continue
        n = len(items)
        agg_rows.append([
            method,
            fmt(sum(d["issue_recall_strict"] for _, d in items) / n),
            fmt(sum(d["issue_recall_loose"] for _, d in items) / n),
            fmt(sum(d["issue_precision"] for _, d in items) / n),
            fmt(sum(d["phantom_rate_strict"] for _, d in items) / n),
            fmt(mean([d["cluster_recall_strict"] for _, d in items if d["cluster_recall_strict"] is not None])),
            fmt(mean([d["phantom_policy_rate"] for _, d in items if d["phantom_policy_rate"] is not None])),
            fmt(mean([d["phantom_num_grounded_rate"] for _, d in items if d["phantom_num_grounded_rate"] is not None])),
            fmt(mean([d["inversion_rate"] for _, d in items])),
            fmt(mean([d["sev_pre_under_rate"] for _, d in items if d["sev_pre_under_rate"] is not None])),
            fmt(mean([d["sev_pre_over_rate"] for _, d in items if d["sev_pre_over_rate"] is not None])),
            fmt(mean([d["decisive_recall"] for _, d in items if d["decisive_recall"] is not None])),
            fmt(mean([d["pos_recall_all"] for _, d in items if d["pos_recall_all"] is not None])),
            fmt(mean([d["pos_recall_pre"] for _, d in items if d["pos_recall_pre"] is not None])),
        ])
    print_table(agg_rows, agg_headers)

    # Micro decisive recall
    print("\n  Decisive recall (micro, pooled):")
    for method in methods:
        total_d = sum(all_results[(method, p)]["decisive_total"] for p in papers if (method, p) in all_results)
        matched_d = sum(all_results[(method, p)]["decisive_matched"] for p in papers if (method, p) in all_results)
        if total_d:
            print(f"    {method}: {matched_d}/{total_d} = {matched_d/total_d:.1%}")

    # ============================================================
    # 2b. v2 artifact filtering + rebuttal-aware summary
    # ============================================================
    if args.exclude_artifacts or args.rebuttal_aware:
        print_section("v2 CONCERN ALIGNMENT METRICS")

        if args.exclude_artifacts:
            print("  Artifact filtering summary:")
            for method in methods:
                items = [(p, all_results[(method, p)]) for p in papers if (method, p) in all_results]
                if not items:
                    continue
                total_art = sum(d["artifact_count"] for _, d in items)
                total_con = sum(d["total_agentic"] + d["artifact_count"] for _, d in items)
                missing = sum(d["artifact_missing_field"] for _, d in items)
                sole = sum(d["sole_match_artifacts"] for _, d in items)
                print(f"    {method}: excluded {total_art}/{total_con} artifacts "
                      f"({100*total_art/total_con:.1f}%)"
                      + (f", {missing} concerns missing field" if missing else "")
                      + (f", {sole} official concerns lost sole match" if sole else ""))

        if args.rebuttal_aware:
            print("\n  Rebuttal-aware tiered recall (macro avg, strict):")
            tier_header = f"    {'method':<25s}  {'Tier-A (all)':<14s}  {'Tier-B (non-res)':<17s}  {'Tier-C (standing)':<18s}"
            print(tier_header)
            print("    " + "-" * (len(tier_header) - 4))
            for method in methods:
                items = [(p, all_results[(method, p)]) for p in papers if (method, p) in all_results]
                if not items:
                    continue
                n = len(items)
                tier_a = sum(d["issue_recall_strict"] for _, d in items) / n
                tier_b_vals = [d["recall_strict_tier_b"] for _, d in items if d["recall_strict_tier_b"] is not None]
                tier_c_vals = [d["recall_strict_tier_c"] for _, d in items if d["recall_strict_tier_c"] is not None]
                tier_b = mean(tier_b_vals) if tier_b_vals else None
                tier_c = mean(tier_c_vals) if tier_c_vals else None
                print(f"    {method:<25s}  {fmt(tier_a):<14s}  {fmt(tier_b):<17s}  {fmt(tier_c):<18s}")

            # Denominator sizes
            print("\n  Denominator sizes (pooled across papers):")
            for method in methods:
                items = [(p, all_results[(method, p)]) for p in papers if (method, p) in all_results]
                if not items:
                    continue
                a = sum(d["tier_a_size"] for _, d in items)
                b = sum(d["tier_b_size"] for _, d in items)
                c = sum(d["tier_c_size"] for _, d in items)
                pdf = sum(d["addressed_in_pdf_count"] for _, d in items)
                print(f"    {method}: tier-a={a}, tier-b={b}, tier-c={c}"
                      + (f", addressed_in_pdf={pdf}" if pdf else ""))
                break  # Same for all methods (official concerns don't change)

            # Per-stratum recall
            print("\n  Per-stratum recall (macro avg, strict):")
            strata_names = ["decisive_blocker", "unresolved", "accepted_limitation", "resolved", "ambiguous"]
            print(f"    {'method':<25s}  " + "  ".join(f"{s:<18s}" for s in strata_names))
            print("    " + "-" * 120)
            for method in methods:
                items = [(p, all_results[(method, p)]) for p in papers if (method, p) in all_results]
                if not items:
                    continue
                vals = []
                for s in strata_names:
                    sv = [d["stratum_recall"].get(s) for _, d in items if d["stratum_recall"].get(s) is not None]
                    vals.append(fmt(mean(sv)) if sv else "n/a")
                print(f"    {method:<25s}  " + "  ".join(f"{v:<18s}" for v in vals))

    # ============================================================
    # 3. Per-paper × method detail table
    # ============================================================
    print_section("PER-PAPER × METHOD DETAIL")
    print(f"{'Paper':<25} {'Method':<15} {'ET':<4} {'Rcl-S':<7} {'Rcl-L':<7} {'Prec':<7} {'Inv':<5} {'Under':<7} {'Over':<7} {'Phant':<7} {'DcRcl':<7}")
    print("-" * 110)
    for paper in papers:
        for method in methods:
            key = (method, paper)
            if key not in all_results:
                continue
            d = all_results[key]
            print(f"{paper:<25} {method:<15} {d['error_type']:<4} "
                  f"{fmt(d['issue_recall_strict']):<7} "
                  f"{fmt(d['issue_recall_loose']):<7} "
                  f"{fmt(d['issue_precision']):<7} "
                  f"{d['judgment_types'].get('inverted', 0):<5} "
                  f"{fmt(d['under_rate']):<7} "
                  f"{fmt(d['over_rate']):<7} "
                  f"{fmt(d['phantom_rate_strict']):<7} "
                  f"{fmt(d['decisive_recall']):<7}")
        print()

    # ============================================================
    # 4. Stratify by error type
    # ============================================================
    print_section("STRATIFIED BY ERROR TYPE")
    by_error: Dict[str, list] = defaultdict(list)
    for (method, paper), d in all_results.items():
        by_error[d["error_type"]].append(d)

    print(f"{'Error Type':<10} {'N':<5} {'Recall':<10} {'Prec':<10} {'Inv Rate':<10} {'Under':<10} {'Over':<10} {'Phantom':<10}")
    print("-" * 75)
    for et in ["TP", "TN", "FP", "FN"]:
        if et in by_error:
            items = by_error[et]
            n = len(items)
            print(f"{et:<10} {n:<5} {fmt(sum(d['issue_recall_strict'] for d in items)/n):<10} "
                  f"{fmt(sum(d['issue_precision'] for d in items)/n):<10} "
                  f"{fmt(sum(d['inversion_rate'] for d in items)/n):<10} "
                  f"{fmt(sum(d['under_rate'] for d in items)/n):<10} "
                  f"{fmt(sum(d['over_rate'] for d in items)/n):<10} "
                  f"{fmt(sum(d['phantom_rate_strict'] for d in items)/n):<10}")

    # ============================================================
    # 5. Stratify by issue_type
    # ============================================================
    print_section("STRATIFIED BY ISSUE TYPE")
    type_counts: Counter = Counter()
    type_matched: Counter = Counter()

    for (method, paper), result in all_results.items():
        official = all_officials[paper]
        matched_ids = set()
        for edge in result["match_edges"]:
            if edge["match_type"] in ("exact", "partial") and edge["official_id"]:
                matched_ids.add(edge["official_id"])
        for c in official.get("concerns", []):
            itype = c.get("issue_type", "unknown")
            type_counts[itype] += 1
            if c["id"] in matched_ids:
                type_matched[itype] += 1

    print(f"{'Issue Type':<15} {'Total':<8} {'Matched':<10} {'Recall':<10} {'Miss Rate':<10}")
    print("-" * 53)
    for itype in sorted(type_counts.keys(), key=lambda k: type_counts[k], reverse=True):
        total = type_counts[itype]
        matched = type_matched[itype]
        recall = matched / total if total else 0
        print(f"{itype:<15} {total:<8} {matched:<10} {fmt(recall):<10} {fmt(1 - recall):<10}")

    # ============================================================
    # 6. Top tags by miss rate
    # ============================================================
    print_section("TOP TAGS BY MISS RATE (min 4 instances)")
    tag_total: Counter = Counter()
    tag_matched: Counter = Counter()
    tag_severity: Dict[str, list] = defaultdict(list)

    for (method, paper), result in all_results.items():
        official = all_officials[paper]
        matched_ids = set()
        for edge in result["match_edges"]:
            if edge["match_type"] in ("exact", "partial") and edge["official_id"]:
                matched_ids.add(edge["official_id"])
                for tag in edge.get("official_tags", []):
                    tag_severity[tag].append(edge.get("severity_alignment", "n/a"))
        for c in official.get("concerns", []):
            for tag in c.get("tags", []):
                tag_total[tag] += 1
                if c["id"] in matched_ids:
                    tag_matched[tag] += 1

    filtered_tags = {t: tag_total[t] for t in tag_total if tag_total[t] >= 4}
    print(f"{'Tag':<35} {'Total':<7} {'Match':<7} {'Miss%':<8} {'Under':<7} {'Over':<7} {'Sev-Match':<10}")
    print("-" * 81)
    for tag in sorted(filtered_tags.keys(), key=lambda t: 1 - (tag_matched[t] / tag_total[t]) if tag_total[t] else 1, reverse=True):
        total = tag_total[tag]
        matched = tag_matched[tag]
        miss = 1 - matched / total if total else 1
        sev_list = tag_severity.get(tag, [])
        sev_eff = [s for s in sev_list if s != "n/a"]
        u = sum(1 for s in sev_eff if s == "under")
        o = sum(1 for s in sev_eff if s == "over")
        m = sum(1 for s in sev_eff if s == "match")
        print(f"{tag:<35} {total:<7} {matched:<7} {fmt(miss):<8} {u:<7} {o:<7} {m:<10}")

    # ============================================================
    # 7. Top tags by severity bias
    # ============================================================
    print_section("TOP TAGS BY SEVERITY UNDER-RATE (min 3 matched)")
    tags_with_sev = {}
    for tag in tag_total:
        sev_list = tag_severity.get(tag, [])
        sev_eff = [s for s in sev_list if s != "n/a"]
        if len(sev_eff) >= 3:
            u = sum(1 for s in sev_eff if s == "under")
            o = sum(1 for s in sev_eff if s == "over")
            m = sum(1 for s in sev_eff if s == "match")
            tags_with_sev[tag] = (u, o, m)

    print(f"{'Tag':<35} {'Under':<7} {'Over':<7} {'Match':<7} {'Under%':<8} {'Over%':<8}")
    print("-" * 74)
    for tag in sorted(tags_with_sev.keys(), key=lambda t: tags_with_sev[t][0] / max(1, sum(tags_with_sev[t])), reverse=True):
        u, o, m = tags_with_sev[tag]
        total_s = u + o + m
        print(f"{tag:<35} {u:<7} {o:<7} {m:<7} {fmt(u/total_s if total_s else 0):<8} {fmt(o/total_s if total_s else 0):<8}")

    # ============================================================
    # 8. Judgment inversions detail
    # ============================================================
    print_section("ALL JUDGMENT INVERSIONS")
    for method in methods:
        for paper in papers:
            key = (method, paper)
            if key not in all_results:
                continue
            for edge in all_results[key]["match_edges"]:
                if edge["judgment_alignment"] == "inverted":
                    print(f"  {method}/{paper}: {edge['official_id']} <-> {edge['agentic_id']} "
                          f"-- official_sev={edge['official_severity']}, "
                          f"ac_treatment={edge['official_ac_treatment']}, "
                          f"tags={edge['official_tags']}")

    # ============================================================
    # 9. Most frequently missed official concerns
    # ============================================================
    print_section("MOST FREQUENTLY MISSED OFFICIAL CONCERNS")
    miss_counter: Counter = Counter()
    miss_details: Dict[str, Dict] = {}
    for method in methods:
        for paper in papers:
            key = (method, paper)
            if key not in all_results:
                continue
            for oid in all_results[key]["unmatched_off_strict"]:
                miss_key = f"{paper}/{oid}"
                miss_counter[miss_key] += 1
                if miss_key not in miss_details:
                    off_concerns = {c["id"]: c for c in all_officials.get(paper, {}).get("concerns", [])}
                    concern = off_concerns.get(oid)
                    if concern:
                        miss_details[miss_key] = {
                            "text": concern.get("text", "")[:80],
                            "severity": concern.get("severity"),
                            "decisive": concern.get("decisive", False),
                            "issue_type": concern.get("issue_type"),
                        }

    print(f"{'Concern':<35} {'Missed':<8} {'Sev':<10} {'Dec':<6} {'Type':<12} {'Text':<60}")
    print("-" * 131)
    for miss_key, count in miss_counter.most_common(25):
        d = miss_details.get(miss_key, {})
        dec = "YES" if d.get("decisive") else ""
        print(f"{miss_key:<35} {count:<8} {d.get('severity', ''):<10} {dec:<6} "
              f"{d.get('issue_type', ''):<12} {d.get('text', ''):<60}")

    # ============================================================
    # 10. Most common phantom concerns
    # ============================================================
    print_section("MOST COMMON PHANTOM CONCERNS (agentic IDs)")
    by_paper_phantoms: Dict[str, list] = defaultdict(list)
    for method in methods:
        for paper in papers:
            key = (method, paper)
            if key not in all_results:
                continue
            for aid in all_results[key]["unmatched_agen_strict"]:
                by_paper_phantoms[paper].append(f"{paper}/{method}/{aid}")

    for paper in papers:
        if paper in by_paper_phantoms:
            print(f"\n  {paper}:")
            for pk in sorted(by_paper_phantoms[paper]):
                print(f"    {pk}")

    # ============================================================
    # 11. Severity pre-calibration (micro, pooled)
    # ============================================================
    print_section("SEVERITY PRE-CALIBRATION (micro, pooled strict edges)")
    for method in methods:
        counts: Counter = Counter()
        total_edges = 0
        for p in papers:
            key = (method, p)
            if key not in all_results:
                continue
            counts.update(all_results[key]["sev_pre_counts"])
            total_edges += sum(all_results[key]["sev_pre_counts"].values())
        if total_edges == 0:
            print(f"  {method}: n/a (no comparable edges)")
            continue
        under = counts.get("under", 0)
        match_c = counts.get("match", 0)
        over = counts.get("over", 0)
        print(
            f"  {method}: under {under}/{total_edges} ({under/total_edges:.1%}), "
            f"match {match_c}/{total_edges} ({match_c/total_edges:.1%}), "
            f"over {over}/{total_edges} ({over/total_edges:.1%})"
        )

    # ============================================================
    # 12. Match type distribution per method
    # ============================================================
    print_section("MATCH TYPE DISTRIBUTION PER METHOD")
    header = f"{'method':<25s}  {'Edges':>6s}  {'Exact':>6s}  {'Exact%':>7s}  {'Partial':>7s}  {'Part%':>7s}  {'Related':>7s}  {'Rel%':>7s}  {'Strict':>7s}  {'Strict%':>7s}"
    print(header)
    print("-" * len(header))
    for method in methods:
        m_exact = m_partial = m_related = 0
        for p in papers:
            key = (method, p)
            if key not in all_results:
                continue
            mt = all_results[key]["match_types"]
            m_exact += mt.get("exact", 0)
            m_partial += mt.get("partial", 0)
            m_related += mt.get("related", 0)
        m_total = m_exact + m_partial + m_related
        m_strict = m_exact + m_partial
        if m_total == 0:
            print(f"  {method}: n/a")
            continue
        print(
            f"{method:<25s}  {m_total:>6d}  {m_exact:>6d}  {m_exact/m_total:>6.1%}  "
            f"{m_partial:>7d}  {m_partial/m_total:>6.1%}  "
            f"{m_related:>7d}  {m_related/m_total:>6.1%}  "
            f"{m_strict:>7d}  {m_strict/m_total:>6.1%}"
        )

    # ============================================================
    # 12b. Summary statistics
    # ============================================================
    print_section("SUMMARY STATISTICS")
    total_edges = sum(sum(d["match_types"].values()) for d in all_results.values())
    total_exact = sum(d["match_types"].get("exact", 0) for d in all_results.values())
    total_partial = sum(d["match_types"].get("partial", 0) for d in all_results.values())
    total_related = sum(d["match_types"].get("related", 0) for d in all_results.values())
    total_inv = sum(d["judgment_types"].get("inverted", 0) for d in all_results.values())
    total_under = sum(d["severity_types"].get("under", 0) for d in all_results.values())
    total_over = sum(d["severity_types"].get("over", 0) for d in all_results.values())
    total_sev_match = sum(d["severity_types"].get("match", 0) for d in all_results.values())

    if total_edges:
        print(f"Total match edges: {total_edges}")
        print(f"  Exact: {total_exact} ({total_exact/total_edges*100:.1f}%)")
        print(f"  Partial: {total_partial} ({total_partial/total_edges*100:.1f}%)")
        print(f"  Related: {total_related} ({total_related/total_edges*100:.1f}%)")
        print(f"Total judgment inversions: {total_inv} ({total_inv/total_edges*100:.1f}%)")
        total_sev_effective = total_under + total_over + total_sev_match
        if total_sev_effective:
            print(f"Severity alignment (excl n/a, N={total_sev_effective}):")
            print(f"  Match: {total_sev_match} ({total_sev_match/total_sev_effective*100:.1f}%)")
            print(f"  Under: {total_under} ({total_under/total_sev_effective*100:.1f}%)")
            print(f"  Over: {total_over} ({total_over/total_sev_effective*100:.1f}%)")


    # ============================================================
    # 13. Phantom diagnostics (micro, pooled)
    # ============================================================
    print_section("PHANTOM DIAGNOSTICS (micro, pooled strict-unmatched agentic concerns)")
    for method in methods:
        total_phantoms = 0
        total_policy = 0
        total_num = 0
        total_num_grounded = 0
        any_paper_text = False
        for p in papers:
            key = (method, p)
            if key not in all_results:
                continue
            d = all_results[key]
            total_phantoms += len(d["unmatched_agen_strict"])
            total_policy += d["phantom_policy_count"]
            total_num += d["phantom_num_total"]
            total_num_grounded += d["phantom_num_grounded"]
            if d.get("has_paper_text"):
                any_paper_text = True
        if total_phantoms == 0:
            print(f"  {method}: n/a (no phantoms)")
            continue
        policy_share = total_policy / total_phantoms if total_phantoms else 0.0
        if not any_paper_text:
            num_rate_str = "n/a (no paper text — use --papers-dir)"
        elif total_num:
            num_rate_str = f"{total_num_grounded}/{total_num} ({total_num_grounded/total_num:.1%})"
        else:
            num_rate_str = "n/a (no numeric phantoms)"
        print(
            f"  {method}: phantoms={total_phantoms}, "
            f"policy_mechanism={total_policy} ({policy_share:.1%} of phantoms), "
            f"num-grounded {num_rate_str}"
        )

    # ============================================================
    # 14. Semantic override summary (if overrides were applied)
    # ============================================================
    if all_overrides is not None:
        print_section("SEMANTIC OVERRIDE SUMMARY")
        total_applied = sum(override_stats_total.values())
        print(f"Edge overrides applied: {total_applied}")
        print(f"  Confirmed (no change): {override_stats_total.get('confirmed', 0)}")
        print(f"  Reclassified: {override_stats_total.get('reclassified', 0)}")
        print(f"  Removed: {override_stats_total.get('removed', 0)}")

        if phantom_judgments_all:
            pj_counts: Counter = Counter(pj.get("judgment", "unknown") for pj in phantom_judgments_all)
            print(f"\nPhantom judgments: {len(phantom_judgments_all)}")
            for jtype in ["grounded", "hallucinated", "policy_artifact", "inconclusive"]:
                c = pj_counts.get(jtype, 0)
                if c:
                    print(f"  {jtype}: {c}")

    # ============================================================
    # 14b. Export per-paper metrics (if --export-per-paper)
    # ============================================================
    if args.export_per_paper:
        export_dir = Path(args.export_per_paper)
        export_dir.mkdir(parents=True, exist_ok=True)

        # Select which fields to export (drop large nested structures)
        EXPORT_FIELDS = [
            "paper", "method", "official_verdict", "agentic_verdict", "error_type",
            "total_official", "total_agentic",
            "issue_recall_strict", "issue_recall_loose", "issue_precision",
            "phantom_rate_strict", "phantom_rate_loose",
            "inversion_rate", "under_rate", "over_rate",
            "decisive_total", "decisive_matched", "decisive_recall",
            "pos_recall_all", "pos_recall_pre",
            "sev_pre_under_rate", "sev_pre_over_rate",
            "cluster_recall_strict",
            "phantom_policy_rate",
            # v2 fields
            "artifact_count", "artifact_missing_field", "sole_match_artifacts", "topk_dropped",
            "tier_a_size", "tier_b_size", "tier_c_size", "addressed_in_pdf_count",
            "recall_strict_tier_b", "recall_loose_tier_b",
            "recall_strict_tier_c", "recall_loose_tier_c",
            "stratum_recall",
        ]

        for method in methods:
            items = [(p, all_results[(method, p)]) for p in papers if (method, p) in all_results]
            if not items:
                continue

            export_data = {
                "schema_version": "clean_metrics_v1",
                "method": method,
                "version": args.version,
                "exclude_artifacts": args.exclude_artifacts,
                "rebuttal_aware": args.rebuttal_aware,
                "top_k": args.top_k,
                "n_papers": len(items),
                "papers": [],
            }
            for paper, d in items:
                row = {}
                for field in EXPORT_FIELDS:
                    val = d.get(field)
                    # Convert sets to sorted lists for YAML serialization
                    if isinstance(val, set):
                        val = sorted(val)
                    # Convert Counter to dict
                    if isinstance(val, Counter):
                        val = dict(val)
                    row[field] = val
                export_data["papers"].append(row)

            out_path = export_dir / f"{method}.yaml"
            out_path.write_text(
                yaml.safe_dump(export_data, sort_keys=False, allow_unicode=True, width=120),
                encoding="utf-8",
            )
            print(f"  Exported {len(items)} papers to {out_path}")

        print(f"\nPer-paper v2 metrics exported to {export_dir}/")

    # ============================================================
    # 15. Human-calibrated metrics (if --human-judgments provided)
    # ============================================================
    if args.human_judgments:
        judgments_dir = Path(args.human_judgments).resolve()
        if not judgments_dir.is_dir():
            print(f"\nWarning: --human-judgments directory not found: {judgments_dir}")
        else:
            human_judgments = load_human_judgments(judgments_dir)
            compute_human_calibrated_metrics(human_judgments, all_results, methods, papers)


if __name__ == "__main__":
    main()
