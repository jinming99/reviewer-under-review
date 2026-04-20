#!/usr/bin/env python3
"""
Lightweight linter for concern-alignment artifacts.

Checks:
  1) severity_alignment sign consistency vs (official severity, agentic severity)
  2) match_type=related should have severity_alignment='n/a' (per Skill 3)
  3) 2-edge cap violations (official_id / agentic_id appears >2 times in matches)
  4) unmatched_official / unmatched_agentic contains IDs that are strictly matched (exact/partial)
  5) positive_factor_matches includes pro_reject factors (Skill 3 says pro_accept only)
  6) Dual-layout detection: works with both pilot layout and calibration/ layout
  7) Same-severity edges must be labeled 'match' (not under/over)
  8) ≥2-level severity gaps must NOT be labeled 'match'
  9) ac_decisive_negative_ids consistency: IDs listed there should have ac_treatment=decisive_blocker
 10) critical_references validation: IDs follow CR\\d+ pattern, role is valid, concern_ids reference existing concerns

Usage:
  python lint_concern_alignment.py --root /path/to/concern_alignment
  python lint_concern_alignment.py --root /path/to/repo_root --version <version>

Discovers papers and methods dynamically from the filesystem.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import yaml

SEV_ORDER = {"minor": 0, "moderate": 1, "major": 2, "fatal": 3}


def _has_artifact_dirs(base: Path) -> bool:
    """Check if base has the three required artifact subdirectories."""
    official = (base / "official").is_dir() or (base / "official_concerns").is_dir()
    agentic = (base / "agentic").is_dir() or (base / "agentic_concerns").is_dir()
    return official and agentic and (base / "match_graphs").is_dir()


def _resolve_dir(base: Path, canonical: str, alt: str) -> Path:
    """Return whichever directory name exists, preferring canonical."""
    if (base / canonical).is_dir():
        return base / canonical
    return base / alt


def detect_artifact_root(root: Path) -> Path:
    """Return the directory containing {official/, agentic/, match_graphs/}.
    Also accepts official_concerns/ and agentic_concerns/ as alternates."""
    root = root.resolve()
    for cand in [root, root / "calibration" / "concern_alignment"]:
        if _has_artifact_dirs(cand):
            return cand
    raise FileNotFoundError(
        f"Could not find artifact dirs under {root}. Expected official/ (or official_concerns/), "
        f"agentic/ (or agentic_concerns/), match_graphs/ either directly or under calibration/concern_alignment/"
    )


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def discover_papers(official_dir: Path) -> list[str]:
    """Discover paper slugs from official/*.yaml."""
    return sorted(p.stem for p in official_dir.glob("*.yaml"))


def discover_methods(agentic_version_dir: Path) -> list[str]:
    """Discover methods from agentic/{version}/ subdirectories."""
    if not agentic_version_dir.is_dir():
        return []
    return sorted(d.name for d in agentic_version_dir.iterdir() if d.is_dir())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Root directory (or repo root) containing concern alignment artifacts")
    ap.add_argument("--version", default="", help="Artifact version folder under agentic/ and match_graphs/. Leave empty for a flat (un-versioned) layout.")
    args = ap.parse_args()

    root = detect_artifact_root(Path(args.root))
    version = args.version

    official_dir = _resolve_dir(root, "official", "official_concerns")
    agentic_base = _resolve_dir(root, "agentic", "agentic_concerns")
    # Support both versioned (agentic/{version}/) and flat (agentic/) layouts
    agentic_ver = agentic_base / version if (agentic_base / version).is_dir() else agentic_base
    papers = discover_papers(official_dir)
    methods = discover_methods(agentic_ver)

    if not papers:
        print(f"No official/*.yaml found under {official_dir}", file=sys.stderr)
        sys.exit(1)
    if not methods:
        print(f"No agentic/{version}/* method dirs found", file=sys.stderr)
        sys.exit(1)

    official = {p: load_yaml(official_dir / f"{p}.yaml") for p in papers}

    # map decision-driver polarity for accepted papers
    driver_pol = {}
    for p in papers:
        for d in official[p].get("ac_decision_drivers", []):
            driver_pol[(p, d["id"])] = d.get("polarity")

    sign_issues = []
    related_sev_issues = []
    cap_issues = []
    unmatched_issues = []
    neg_factor_issues = []
    pro_reject_mention_issues = []
    same_sev_issues = []      # both same severity but labeled under/over
    tolerance_issues = []     # ≥2-level gap labeled match
    decisive_id_issues = []   # ac_decisive_negative_ids vs ac_treatment mismatch
    cr_issues = []            # critical_references validation

    mg_base = root / "match_graphs" / version if (root / "match_graphs" / version).is_dir() else root / "match_graphs"

    for method in methods:
        for paper in papers:
            mg_path = mg_base / method / f"{paper}.yaml"
            ag_path = agentic_ver / method / f"{paper}.yaml"
            if not mg_path.exists() or not ag_path.exists():
                continue

            mg = load_yaml(mg_path)
            ag = load_yaml(ag_path)

            # Check for pro_reject mentions (Skill 2 hard rule: negative critiques
            # belong in concerns[], not mentions[])
            for m in (ag.get("mentions") or []):
                if isinstance(m, dict) and m.get("polarity") == "pro_reject":
                    pro_reject_mention_issues.append((
                        method, paper, m.get("id", "?"),
                        (m.get("text") or "")[:80],
                    ))

            # build severity lookup tables
            off_sev = {}
            off_treat = {}
            for c in official[paper].get("concerns", []):
                off_sev[c["id"]] = c.get("severity")
                off_treat[c["id"]] = c.get("ac_treatment")

            ag_sev = {}
            for c in ag.get("concerns", []):
                lvl = (c.get("severity") or {}).get("level")
                ag_sev[c["id"]] = lvl

            matches = mg.get("matches", []) or []
            off_count = {}
            ag_count = {}

            matched_off_strict = set()
            matched_ag_strict = set()

            for e in matches:
                oid = e["official_id"]; aid = e["agentic_id"]
                off_count[oid] = off_count.get(oid, 0) + 1
                ag_count[aid] = ag_count.get(aid, 0) + 1

                if e.get("match_type") == "related" and e.get("severity_alignment") not in ("n/a", None):
                    related_sev_issues.append((method, paper, oid, aid, e.get("severity_alignment")))

                if e.get("match_type") in ("exact", "partial"):
                    matched_off_strict.add(oid)
                    matched_ag_strict.add(aid)

                # sign check (only if both severities present and recorded severity_alignment not n/a)
                sa = e.get("severity_alignment")
                if sa in (None, "n/a"):
                    continue

                o_lvl = off_sev.get(oid)
                a_lvl = ag_sev.get(aid)
                if o_lvl not in SEV_ORDER or a_lvl not in SEV_ORDER:
                    continue
                o = SEV_ORDER[o_lvl]; a = SEV_ORDER[a_lvl]

                # Skill 3: reframed_feature treated as non-blocking
                if off_treat.get(oid) == "reframed_feature":
                    o = -1

                if a < o and sa == "over":
                    sign_issues.append((method, paper, oid, aid, o_lvl, a_lvl, off_treat.get(oid), sa))
                if a > o and sa == "under":
                    sign_issues.append((method, paper, oid, aid, o_lvl, a_lvl, off_treat.get(oid), sa))

                # Check 7: same severity labeled as under/over
                if o == a and sa in ("under", "over"):
                    same_sev_issues.append((method, paper, oid, aid, o_lvl, a_lvl, sa, "should be match"))

                # Check 8: ≥2-level gap labeled as match
                if abs(o - a) >= 2 and sa == "match":
                    expected = "under" if a < o else "over"
                    tolerance_issues.append((method, paper, oid, aid, o_lvl, a_lvl, sa, f"should be {expected}"))

            # cap violations
            for oid, c in off_count.items():
                if c > 2:
                    cap_issues.append((method, paper, "official", oid, c))
            for aid, c in ag_count.items():
                if c > 2:
                    cap_issues.append((method, paper, "agentic", aid, c))

            # unmatched list consistency (strict matches only)
            unmatched_off = set(mg.get("unmatched_official", []) or [])
            unmatched_ag = set(mg.get("unmatched_agentic", []) or [])

            for oid in unmatched_off & matched_off_strict:
                unmatched_issues.append((method, paper, "unmatched_official_but_matched", oid))
            for aid in unmatched_ag & matched_ag_strict:
                unmatched_issues.append((method, paper, "unmatched_agentic_but_matched", aid))

            # negative decision drivers inside positive_factor_matches
            for f in mg.get("positive_factor_matches", []) or []:
                fid = f.get("official_factor_id")
                if driver_pol.get((paper, fid)) == "pro_reject":
                    neg_factor_issues.append((method, paper, fid, f.get("match_type")))

    # Check 9: ac_decisive_negative_ids consistency
    for paper in papers:
        off = official[paper]
        decisive_ids = set(off.get("ac_decisive_negative_ids") or [])
        concern_map = {c["id"]: c for c in off.get("concerns", [])}
        for cid in decisive_ids:
            if cid in concern_map:
                treat = concern_map[cid].get("ac_treatment")
                if treat not in ("decisive_blocker",):
                    decisive_id_issues.append((
                        paper, cid, treat,
                        "listed in ac_decisive_negative_ids but ac_treatment is not decisive_blocker"
                    ))

    # Check 10: critical_references validation
    VALID_CR_ROLES = {"missing_comparison", "novelty_precedent", "methodological_basis",
                      "methodological_precedent", "methodology_precedent",
                      "methodology_reference", "positive_positioning", "missing_citation",
                      "benchmark_precedent", "unfavorable_comparison",
                      "prior_art_undermining_novelty", "undermining_claim",
                      "supporting_evidence", "presentation_reference"}
    for paper in papers:
        off = official[paper]
        concern_ids_set = {c["id"] for c in off.get("concerns", [])}
        for cr in off.get("critical_references") or []:
            cr_id = cr.get("id", "?")
            # ID pattern
            if not isinstance(cr_id, str) or not cr_id.startswith("CR"):
                cr_issues.append((paper, cr_id, "id does not match CR\\d+ pattern"))
            # Role validation
            role = cr.get("role")
            if role not in VALID_CR_ROLES:
                cr_issues.append((paper, cr_id, f"invalid role '{role}'"))
            # concern_ids reference existing concerns
            for ref_cid in cr.get("concern_ids") or []:
                if ref_cid not in concern_ids_set:
                    cr_issues.append((paper, cr_id, f"concern_id '{ref_cid}' not found in concerns"))

    def print_block(title, items, max_show=50):
        print("\n" + "=" * len(title))
        print(title)
        print("=" * len(title))
        print(f"count: {len(items)}")
        for row in items[:max_show]:
            print(" -", row)
        if len(items) > max_show:
            print(f"... ({len(items) - max_show} more)")

    print_block("SEVERITY_ALIGNMENT SIGN ISSUES", sign_issues)
    print_block("RELATED MATCHES WITH SEVERITY_ALIGNMENT SET", related_sev_issues)
    print_block("EDGE CAP VIOLATIONS", cap_issues)
    print_block("UNMATCHED LIST INCONSISTENCIES (STRICT)", unmatched_issues)
    print_block("PRO_REJECT FACTORS IN positive_factor_matches", neg_factor_issues)
    print_block("PRO_REJECT MENTIONS IN AGENTIC SHEETS (Skill 2 violation: should be concerns)", pro_reject_mention_issues)
    print_block("SAME SEVERITY LABELED AS UNDER/OVER", same_sev_issues)
    print_block("≥2-LEVEL GAP LABELED AS MATCH", tolerance_issues)
    print_block("AC_DECISIVE_NEGATIVE_IDS vs AC_TREATMENT MISMATCH", decisive_id_issues)
    print_block("CRITICAL_REFERENCES VALIDATION", cr_issues)

    # nonzero exit if anything found (pro_reject mentions are warnings, not hard failures — excluded from exit code)
    total = sum(len(x) for x in [sign_issues, related_sev_issues, cap_issues, unmatched_issues, neg_factor_issues,
                                  same_sev_issues, tolerance_issues, decisive_id_issues, cr_issues])
    warnings = len(pro_reject_mention_issues)
    if warnings:
        print(f"\nWarnings: {warnings} (pro_reject mentions — not blocking, but should be migrated to concerns)")
    print(f"\nTotal issues: {total}")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
