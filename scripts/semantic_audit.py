#!/usr/bin/env python3
"""
Semantic audit helpers for concern-alignment artifacts.

This is NOT the main evaluation script. It provides a lightweight, deterministic
way to find *candidate* label issues that an LLM-based verifier (or a human)
should inspect first.

What it does:
  1) Flags strict match edges (exact/partial) whose official vs agentic concern
     texts have very low lexical overlap. These are common sources of
     "partial-vs-related" label drift.
  2) Flags phantom (strict-unmatched) agentic concerns that include explicit
     numeric claims, but none of those numbers appear in the paper PDF text
     (if papers/ is available). This is a *lower-bound* groundedness check.

Important:
  - Low lexical overlap does NOT imply a wrong match. It just means "inspect".
  - Numeric non-match also does NOT prove hallucination (OCR issues, rounding,
    or numbers in figures can cause misses). It means "inspect".

Recommended workflow:
  - Run this script to generate a short review queue.
  - Only then run an LLM verifier on the queued items (keeps things simple and cheap).
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None  # type: ignore


STOPWORDS = {
    # minimal stopword set (avoid dependency on nltk)
    "a","an","the","and","or","but","if","then","than","to","of","in","on","for","with","without",
    "is","are","was","were","be","been","being","as","at","by","from","that","this","these","those",
    "it","its","they","their","we","our","you","your","i","he","she","his","her","them",
    "not","no","yes","do","does","did","done","can","could","should","would","may","might","must",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")

# Matches integers or decimals, optionally followed by %, at word boundaries.
# NOTE: substring matching downstream is naive ("3" matches inside "300").
# This is acceptable for a conservative lower-bound check; false negatives
# in flagging (concluding a number is "found" when it's part of a different
# number) reduce the flag rate but don't produce false alarms.
NUM_RE = re.compile(r"(?<!\w)(\d+(?:\.\d+)?)%?(?!\w)")


def tokenize(s: str) -> Set[str]:
    toks = set(TOKEN_RE.findall((s or "").lower()))
    return {t for t in toks if t not in STOPWORDS and len(t) > 2}


def jaccard(a: str, b: str) -> float:
    ta, tb = tokenize(a), tokenize(b)
    # Guard: if both token sets are empty (very short texts), return 0
    # but don't flag — caller should check min token count separately
    if not ta and not tb:
        return 0.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# Minimum number of content tokens (after stopword removal) for a concern
# text to be eligible for Jaccard-based flagging. Texts below this threshold
# are too short to produce meaningful overlap scores.
MIN_TOKENS_FOR_SIM = 3


def numbers_in_text(s: str) -> Set[str]:
    return set(NUM_RE.findall(s or ""))


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _exists_dir(p: Path) -> bool:
    return p.exists() and p.is_dir()


def detect_artifact_root(root: Path) -> Path:
    root = root.resolve()
    if _exists_dir(root / "official") and _exists_dir(root / "agentic") and _exists_dir(root / "match_graphs"):
        return root
    cand = root / "calibration" / "concern_alignment"
    if _exists_dir(cand / "official") and _exists_dir(cand / "agentic") and _exists_dir(cand / "match_graphs"):
        return cand
    for sub in (root.iterdir() if root.exists() else []):
        if sub.is_dir() and _exists_dir(sub / "official") and _exists_dir(sub / "agentic") and _exists_dir(sub / "match_graphs"):
            return sub
    raise FileNotFoundError(f"Could not find artifact dirs under {root}")


def detect_latest_version(agentic_dir: Path) -> str:
    """Auto-detect the latest version directory under agentic/."""
    versions = sorted(
        [d.name for d in agentic_dir.iterdir() if d.is_dir() and d.name.startswith("v")],
        reverse=True,
    )
    if versions:
        return versions[0]
    raise FileNotFoundError(
        f"No version directories found under {agentic_dir}. "
        f"Pass --version explicitly if the artifact tree is flat (un-versioned)."
    )


def extract_pdf_text(path: Path, max_pages: Optional[int] = None) -> str:
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


def index_by_id(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for it in items:
        if isinstance(it, dict) and it.get("id"):
            out[str(it["id"])] = it
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Semantic audit for concern-alignment artifacts.")
    ap.add_argument("--root", type=str, default=".")
    ap.add_argument("--version", type=str, default=None,
                    help="Artifact version (default: auto-detect latest).")
    ap.add_argument("--exact_min_sim", type=float, default=0.05,
                    help="Flag exact edges below this Jaccard similarity.")
    ap.add_argument("--partial_min_sim", type=float, default=0.00,
                    help="Flag partial edges <= this Jaccard similarity.")
    ap.add_argument("--paper_text_max_pages", type=int, default=None)
    ap.add_argument("--max_list", type=int, default=40,
                    help="Max flagged items to print per section.")
    ap.add_argument("--papers_dir", type=str, default=None,
                    help="Directory containing {paper}.pdf files for groundedness check. "
                         "Defaults to <artifact_root>/papers/ if present.")
    ap.add_argument("--output-queue", type=str, default=None,
                    help="Write structured YAML queue for Skill 5 consumption instead of "
                         "(in addition to) stdout. Contains flagged_edges and flagged_phantoms.")
    args = ap.parse_args()

    artifact_root = detect_artifact_root(Path(args.root))
    official_dir = artifact_root / "official"
    agentic_base = artifact_root / "agentic"

    # Auto-detect version if not specified
    version = args.version or detect_latest_version(agentic_base)

    agentic_dir = agentic_base / version
    match_dir = artifact_root / "match_graphs" / version
    papers_dir = Path(args.papers_dir) if args.papers_dir else artifact_root / "papers"

    papers = sorted([p.stem for p in official_dir.glob("*.yaml")])
    methods = sorted([d.name for d in agentic_dir.iterdir() if d.is_dir()])

    # Preload paper text (optional)
    paper_text: Dict[str, str] = {}
    if papers_dir.exists() and PdfReader is not None:
        for paper in papers:
            pdf = papers_dir / f"{paper}.pdf"
            if pdf.exists():
                paper_text[paper] = extract_pdf_text(pdf, max_pages=args.paper_text_max_pages)

    # 1) Flag low-sim strict edges
    flagged_edges: List[Tuple[str,str,str,str,str,float]] = []  # method,paper,oid,aid,match_type,sim
    edge_counts: Counter = Counter()

    for paper in papers:
        off = load_yaml(official_dir / f"{paper}.yaml")
        off_idx = index_by_id(off.get("concerns") or [])
        for method in methods:
            apath = agentic_dir / method / f"{paper}.yaml"
            mpath = match_dir / method / f"{paper}.yaml"
            if not apath.exists() or not mpath.exists():
                continue
            ag = load_yaml(apath)
            ag_idx = index_by_id(ag.get("concerns") or [])
            mg = load_yaml(mpath)
            for e in (mg.get("matches") or []):
                mt = e.get("match_type")
                if mt not in ("exact","partial"):
                    continue
                oid, aid = e.get("official_id"), e.get("agentic_id")
                if oid not in off_idx or aid not in ag_idx:
                    continue
                off_text = off_idx[oid].get("text") or ""
                ag_text = ag_idx[aid].get("text") or ""
                # Skip pairs where either text is too short for meaningful similarity
                if len(tokenize(off_text)) < MIN_TOKENS_FOR_SIM or len(tokenize(ag_text)) < MIN_TOKENS_FOR_SIM:
                    continue
                sim = jaccard(off_text, ag_text)
                edge_counts[(method,mt)] += 1
                if mt == "exact" and sim < args.exact_min_sim:
                    flagged_edges.append((method,paper,oid,aid,mt,sim))
                if mt == "partial" and sim <= args.partial_min_sim:
                    flagged_edges.append((method,paper,oid,aid,mt,sim))

    print(f"\n{'='*70}")
    print(f"SEMANTIC AUDIT: LOW-OVERLAP STRICT EDGES (inspect queue) [version={version}]")
    print("="*70)
    for method in methods:
        exact_total = edge_counts.get((method,"exact"),0)
        partial_total = edge_counts.get((method,"partial"),0)
        flagged = [x for x in flagged_edges if x[0]==method]
        print(f"{method}: strict edges exact={exact_total}, partial={partial_total}, flagged={len(flagged)}")

    flagged_edges_sorted = sorted(flagged_edges, key=lambda x: (x[0], x[4], x[5]))
    print("\n-- Flagged edge list (truncated) --")
    for row in flagged_edges_sorted[:args.max_list]:
        method,paper,oid,aid,mt,sim=row
        print(f"{method}/{paper}: {oid} <-> {aid} ({mt}), sim={sim:.3f}")

    # 2) Phantom numeric groundedness misses
    if paper_text:
        phantom_misses: List[Tuple[str,str,str,List[str]]] = []  # method,paper,aid,nums
        for paper in papers:
            ptxt = paper_text.get(paper, "")
            for method in methods:
                apath = agentic_dir / method / f"{paper}.yaml"
                mpath = match_dir / method / f"{paper}.yaml"
                if not apath.exists() or not mpath.exists():
                    continue
                ag = load_yaml(apath)
                ag_idx = index_by_id(ag.get("concerns") or [])
                mg = load_yaml(mpath)
                strict_matched = {e.get("agentic_id") for e in (mg.get("matches") or []) if e.get("match_type") in ("exact","partial")}
                for aid, c in ag_idx.items():
                    if aid in strict_matched:
                        continue
                    nums = sorted(numbers_in_text(c.get("text") or ""))
                    if not nums:
                        continue
                    if not any(n in ptxt for n in nums):
                        phantom_misses.append((method,paper,aid,nums))

        print(f"\n{'='*70}")
        print("SEMANTIC AUDIT: PHANTOM NUMERIC CLAIMS NOT FOUND IN PAPER TEXT")
        print("="*70)
        miss_by_method: Counter = Counter([m for m,_,_,_ in phantom_misses])
        for method in methods:
            print(f"{method}: {miss_by_method.get(method,0)} flagged phantoms")

        print("\n-- Flagged phantom list (truncated) --")
        for row in phantom_misses[:args.max_list]:
            method,paper,aid,nums=row
            print(f"{method}/{paper}: {aid} nums={nums[:6]}" + ("..." if len(nums)>6 else ""))
    else:
        print("\n(note) papers/ not found or PDF extraction unavailable; skipping phantom numeric groundedness audit.")
        phantom_misses = []

    # Write structured queue YAML if requested
    if args.output_queue:
        queue: Dict[str, Any] = {
            "schema_version": "v1",
            "version": version,
            "flagged_edges": [
                {
                    "method": row[0],
                    "paper": row[1],
                    "official_id": row[2],
                    "agentic_id": row[3],
                    "match_type": row[4],
                    "jaccard_sim": round(row[5], 4),
                }
                for row in flagged_edges_sorted
            ],
            "flagged_phantoms": [
                {
                    "method": row[0],
                    "paper": row[1],
                    "agentic_id": row[2],
                    "unfound_numbers": row[3],
                }
                for row in phantom_misses
            ],
        }
        out_path = Path(args.output_queue)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            yaml.dump(queue, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"\nQueue written to {out_path} ({len(queue['flagged_edges'])} edges, {len(queue['flagged_phantoms'])} phantoms)")


if __name__ == "__main__":
    main()
