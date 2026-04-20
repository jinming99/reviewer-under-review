#!/usr/bin/env python3
"""Generate audit worksheets for concern alignment match graph verification.

Produces a markdown worksheet with side-by-side concern texts for every strict
edge and every unmatched concern, ready for an independent verifier (Skill 5b)
to judge.

Usage:
    python scripts/generate_audit_worksheet.py \
        --version <version> --method <method> --paper <paper_slug> \
        --output reports/worksheets/<version>/<method>/<paper_slug>.md

    # With optional Jaccard flag queue from semantic_audit.py
    python scripts/generate_audit_worksheet.py \
        --version <version> --method <method> --paper <paper_slug> \
        --output reports/worksheets/<version>/<method>/<paper_slug>.md \
        --flagged-queue tmp/queue.yaml

    # Batch mode: all papers for a version/method
    python scripts/generate_audit_worksheet.py \
        --version <version> --method <method> --all \
        --output-dir reports/worksheets/<version>/<method>/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file, raising a clear error if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _concern_text(concern: Dict[str, Any]) -> str:
    """Extract the one-line concern text."""
    return concern.get("text", "(no text)")


def _concern_severity(concern: Dict[str, Any], is_agentic: bool = False) -> str:
    """Extract severity string from official or agentic concern."""
    if is_agentic:
        sev = concern.get("severity", {})
        if isinstance(sev, dict):
            return sev.get("level", "unknown")
        return str(sev)
    return concern.get("severity", "unknown")


def _build_concern_lookup(
    concerns: List[Dict[str, Any]], is_agentic: bool = False
) -> Dict[str, Dict[str, Any]]:
    """Build id -> concern dict."""
    lookup: Dict[str, Dict[str, Any]] = {}
    for c in concerns:
        cid = c.get("id", "")
        lookup[cid] = {
            "id": cid,
            "text": _concern_text(c),
            "severity": _concern_severity(c, is_agentic),
            "tags": c.get("tags", []),
        }
        if is_agentic:
            sev_obj = c.get("severity", {})
            if isinstance(sev_obj, dict):
                lookup[cid]["addressability"] = sev_obj.get("addressability", "unknown")
            lookup[cid]["decisive"] = c.get("decisive", False)
            lookup[cid]["source"] = c.get("source", "")
    return lookup


def _jaccard(a: str, b: str) -> float:
    """Word-level Jaccard similarity between two strings."""
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _load_flagged_queue(path: Optional[Path]) -> Dict[Tuple[str, str, str, str], float]:
    """Load flagged queue and return (method, paper, oid, aid) -> jaccard_sim."""
    if path is None or not path.exists():
        return {}
    data = _load_yaml(path)
    result: Dict[Tuple[str, str, str, str], float] = {}
    for edge in data.get("flagged_edges", []):
        key = (edge["method"], edge["paper"], edge["official_id"], edge["agentic_id"])
        result[key] = edge.get("jaccard_sim", 0.0)
    return result


# ---------------------------------------------------------------------------
# Worksheet generation
# ---------------------------------------------------------------------------

def generate_worksheet(
    match_graph: Dict[str, Any],
    official_sheet: Dict[str, Any],
    agentic_sheet: Dict[str, Any],
    flagged_queue: Dict[Tuple[str, str, str, str], float],
    paper: str,
    method: str,
    version: str,
) -> str:
    """Generate a markdown audit worksheet for one (paper, method) pair."""

    official_concerns = _build_concern_lookup(
        official_sheet.get("concerns", []), is_agentic=False
    )
    agentic_concerns = _build_concern_lookup(
        agentic_sheet.get("concerns", []), is_agentic=True
    )

    matches = match_graph.get("matches", [])
    unmatched_official_ids = match_graph.get("unmatched_official", [])
    unmatched_agentic_ids = match_graph.get("unmatched_agentic", [])

    # Separate strict (exact/partial) from related edges
    strict_edges = [m for m in matches if m.get("match_type") in ("exact", "partial")]
    related_edges = [m for m in matches if m.get("match_type") == "related"]

    # Validation: check all IDs resolve
    errors: List[str] = []
    for edge in matches:
        oid = edge.get("official_id", "")
        aid = edge.get("agentic_id", "")
        if oid not in official_concerns:
            errors.append(f"Edge {oid}↔{aid}: official_id '{oid}' not found in official concern sheet")
        if aid not in agentic_concerns:
            errors.append(f"Edge {oid}↔{aid}: agentic_id '{aid}' not found in agentic concern sheet")
    for uid in unmatched_official_ids:
        if uid not in official_concerns:
            errors.append(f"unmatched_official '{uid}' not found in official concern sheet")
    for uid in unmatched_agentic_ids:
        if uid not in agentic_concerns:
            errors.append(f"unmatched_agentic '{uid}' not found in agentic concern sheet")

    if errors:
        raise ValueError(
            f"ID resolution errors for {paper}/{method}:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    lines: List[str] = []

    # --- Header ---
    lines.append(f"# Audit Worksheet: {paper} / {method} / {version}")
    lines.append("")
    lines.append(f"**Paper**: {official_sheet.get('title', paper)}")
    lines.append(f"**Official verdict**: {official_sheet.get('official_verdict', 'unknown')}")
    lines.append(f"**Agentic verdict**: {agentic_sheet.get('verdict', 'unknown')} (score: {agentic_sheet.get('score', 'n/a')})")
    lines.append("")
    lines.append("| Count | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| Strict edges (exact/partial) | {len(strict_edges)} |")
    lines.append(f"| Related edges | {len(related_edges)} |")
    lines.append(f"| Unmatched official | {len(unmatched_official_ids)} |")
    lines.append(f"| Unmatched agentic | {len(unmatched_agentic_ids)} |")
    lines.append(f"| Total official concerns | {len(official_concerns)} |")
    lines.append(f"| Total agentic concerns | {len(agentic_concerns)} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- Section 1: Strict edges ---
    lines.append("## Section 1: Strict Edges (exact/partial)")
    lines.append("")
    if not strict_edges:
        lines.append("*No strict edges in this match graph.*")
        lines.append("")
    else:
        for i, edge in enumerate(strict_edges, 1):
            oid = edge["official_id"]
            aid = edge["agentic_id"]
            mt = edge.get("match_type", "?")
            ja = edge.get("judgment_alignment", "?")
            sa = edge.get("severity_alignment", "?")
            rationale = edge.get("rationale", "(no rationale)")
            issue = edge.get("issue", "")

            o_info = official_concerns.get(oid, {})
            a_info = agentic_concerns.get(aid, {})

            # Get Jaccard from queue or compute on the fly
            queue_key = (method, paper, oid, aid)
            if queue_key in flagged_queue:
                jaccard_score = flagged_queue[queue_key]
                flagged_str = " **[FLAGGED]**"
            else:
                jaccard_score = _jaccard(o_info.get("text", ""), a_info.get("text", ""))
                flagged_str = ""

            lines.append(f"### Edge {i}: {oid} ↔ {aid} [{mt}]{flagged_str}")
            lines.append("")
            lines.append(f"**Issue**: {issue}")
            lines.append("")
            lines.append(f"| | Official ({oid}) | Agentic ({aid}) |")
            lines.append("|---|---|---|")
            lines.append(f"| **Text** | {o_info.get('text', '?')} | {a_info.get('text', '?')} |")
            lines.append(f"| **Severity** | {o_info.get('severity', '?')} | {a_info.get('severity', '?')} |")
            lines.append(f"| **Tags** | {', '.join(o_info.get('tags', []))} | {', '.join(a_info.get('tags', []))} |")
            lines.append("")
            lines.append(f"- **Match type**: `{mt}`")
            lines.append(f"- **Judgment alignment**: `{ja}`")
            lines.append(f"- **Severity alignment**: `{sa}`")
            lines.append(f"- **Jaccard similarity**: {jaccard_score:.3f}")
            lines.append(f"- **Rationale**: {rationale}")
            lines.append("")
            lines.append("**Verification verdict**: _(to be filled by verifier)_")
            lines.append("")
            lines.append("- Match type correct? `[ ]` yes / `[ ]` reclassify to: ___")
            lines.append("- Judgment alignment correct? `[ ]` yes / `[ ]` reclassify to: ___")
            lines.append("- Severity alignment correct? `[ ]` yes / `[ ]` reclassify to: ___")
            lines.append("- Action: `[ ]` confirmed / `[ ]` reclassified / `[ ]` removed")
            lines.append("")

    lines.append("---")
    lines.append("")

    # --- Section 2: Unmatched official concerns ---
    lines.append("## Section 2: Unmatched Official Concerns")
    lines.append("")
    if not unmatched_official_ids:
        lines.append("*All official concerns have strict matches.*")
        lines.append("")
    else:
        for uid in unmatched_official_ids:
            o_info = official_concerns.get(uid, {})
            lines.append(f"### {uid} (unmatched)")
            lines.append("")
            lines.append(f"**Text**: {o_info.get('text', '?')}")
            lines.append(f"**Severity**: {o_info.get('severity', '?')}")
            lines.append(f"**Tags**: {', '.join(o_info.get('tags', []))}")
            lines.append("")

            # Rank all agentic concerns by Jaccard similarity for comparison
            scored: List[Tuple[float, str, Dict[str, Any]]] = []
            for aid, a_info in agentic_concerns.items():
                sim = _jaccard(o_info.get("text", ""), a_info.get("text", ""))
                scored.append((sim, aid, a_info))
            scored.sort(key=lambda x: -x[0])

            lines.append("**Candidate agentic comparisons** (ranked by Jaccard):")
            lines.append("")
            lines.append("| Rank | ID | Jaccard | Text | Severity |")
            lines.append("|------|-----|---------|------|----------|")
            for rank, (sim, aid, a_info) in enumerate(scored[:5], 1):
                lines.append(
                    f"| {rank} | {aid} | {sim:.3f} | {a_info.get('text', '?')} | {a_info.get('severity', '?')} |"
                )
            lines.append("")
            lines.append("**Verification verdict**: _(to be filled by verifier)_")
            lines.append("")
            lines.append("- Missed match? `[ ]` no (correctly unmatched) / `[ ]` yes → match with: ___ (type: ___)")
            lines.append("")

    lines.append("---")
    lines.append("")

    # --- Section 3: Unmatched agentic concerns ---
    lines.append("## Section 3: Unmatched Agentic Concerns")
    lines.append("")
    if not unmatched_agentic_ids:
        lines.append("*All agentic concerns have strict matches.*")
        lines.append("")
    else:
        for uid in unmatched_agentic_ids:
            a_info = agentic_concerns.get(uid, {})
            lines.append(f"### {uid} (unmatched — phantom candidate)")
            lines.append("")
            lines.append(f"**Text**: {a_info.get('text', '?')}")
            lines.append(f"**Severity**: {a_info.get('severity', '?')}")
            lines.append(f"**Source**: {a_info.get('source', '?')}")
            lines.append(f"**Decisive**: {a_info.get('decisive', False)}")
            lines.append(f"**Tags**: {', '.join(a_info.get('tags', []))}")
            lines.append("")

            # Rank all official concerns by Jaccard similarity for comparison
            scored = []
            for oid, o_info in official_concerns.items():
                sim = _jaccard(a_info.get("text", ""), o_info.get("text", ""))
                scored.append((sim, oid, o_info))
            scored.sort(key=lambda x: -x[0])

            lines.append("**Candidate official comparisons** (ranked by Jaccard):")
            lines.append("")
            lines.append("| Rank | ID | Jaccard | Text | Severity |")
            lines.append("|------|-----|---------|------|----------|")
            for rank, (sim, oid, o_info) in enumerate(scored[:5], 1):
                lines.append(
                    f"| {rank} | {oid} | {sim:.3f} | {o_info.get('text', '?')} | {o_info.get('severity', '?')} |"
                )
            lines.append("")
            lines.append("**Verification verdict**: _(to be filled by verifier)_")
            lines.append("")
            lines.append("- Missed match? `[ ]` no (true phantom) / `[ ]` yes → match with: ___ (type: ___)")
            lines.append("")

    # --- Section 4: Related edges (informational) ---
    if related_edges:
        lines.append("---")
        lines.append("")
        lines.append("## Section 4: Related Edges (informational — not scored)")
        lines.append("")
        for edge in related_edges:
            oid = edge["official_id"]
            aid = edge["agentic_id"]
            o_info = official_concerns.get(oid, {})
            a_info = agentic_concerns.get(aid, {})
            rationale = edge.get("rationale", "(no rationale)")

            lines.append(f"- **{oid} ↔ {aid}** [related]: {o_info.get('text', '?')} ↔ {a_info.get('text', '?')}")
            lines.append(f"  - Rationale: {rationale}")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def _find_root() -> Path:
    """Find the repo root (directory containing CLAUDE.md)."""
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / "CLAUDE.md").exists():
            return parent
    return cwd


def _resolve_paths(
    root: Path, version: str, method: str, paper: str
) -> Tuple[Path, Path, Path]:
    """Resolve paths for match graph, official sheet, agentic sheet."""
    mg_path = root / "calibration" / "concern_alignment" / "match_graphs" / version / method / f"{paper}.yaml"
    off_path = root / "calibration" / "concern_alignment" / "official" / f"{paper}.yaml"
    ag_path = root / "calibration" / "concern_alignment" / "agentic" / version / method / f"{paper}.yaml"
    return mg_path, off_path, ag_path


def _discover_papers(root: Path, version: str, method: str) -> List[str]:
    """Discover all papers with match graphs for a version/method."""
    mg_dir = root / "calibration" / "concern_alignment" / "match_graphs" / version / method
    if not mg_dir.exists():
        return []
    return sorted(p.stem for p in mg_dir.glob("*.yaml"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate audit worksheets for match graph verification."
    )
    parser.add_argument("--version", required=True, help="Artifact version folder name (arbitrary string)")
    parser.add_argument("--method", required=True, help="Method name (e.g. baseline)")
    parser.add_argument("--paper", default=None, help="Paper slug (omit with --all)")
    parser.add_argument("--all", action="store_true", dest="all_papers",
                        help="Generate worksheets for all papers in this version/method")
    parser.add_argument("--output", default=None, help="Output path for single paper")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for batch mode (--all)")
    parser.add_argument("--flagged-queue", default=None,
                        help="Path to semantic_audit.py --output-queue YAML (advisory)")
    args = parser.parse_args()

    root = _find_root()

    # Determine paper list
    if args.all_papers:
        papers = _discover_papers(root, args.version, args.method)
        if not papers:
            print(f"No match graphs found for {args.version}/{args.method}", file=sys.stderr)
            sys.exit(1)
        if not args.output_dir:
            args.output_dir = str(
                root / "calibration" / "concern_alignment" / "reports"
                / "worksheets" / args.version / args.method
            )
    elif args.paper:
        papers = [args.paper]
    else:
        print("Specify --paper or --all", file=sys.stderr)
        sys.exit(1)

    # Load flagged queue if provided
    flagged_queue = _load_flagged_queue(
        Path(args.flagged_queue) if args.flagged_queue else None
    )

    success = 0
    failures: List[Tuple[str, str]] = []

    for paper in papers:
        try:
            mg_path, off_path, ag_path = _resolve_paths(root, args.version, args.method, paper)
            match_graph = _load_yaml(mg_path)
            official_sheet = _load_yaml(off_path)
            agentic_sheet = _load_yaml(ag_path)

            worksheet = generate_worksheet(
                match_graph=match_graph,
                official_sheet=official_sheet,
                agentic_sheet=agentic_sheet,
                flagged_queue=flagged_queue,
                paper=paper,
                method=args.method,
                version=args.version,
            )

            # Determine output path
            if args.output and len(papers) == 1:
                out_path = Path(args.output)
            elif args.output_dir:
                out_path = Path(args.output_dir) / f"{paper}.md"
            else:
                out_path = (
                    root / "calibration" / "concern_alignment" / "reports"
                    / "worksheets" / args.version / args.method / f"{paper}.md"
                )

            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(worksheet)
            success += 1

        except Exception as e:
            failures.append((paper, str(e)))
            print(f"ERROR [{paper}]: {e}", file=sys.stderr)

    # Summary
    print(f"\nWorksheet generation complete: {success}/{len(papers)} succeeded")
    if failures:
        print(f"Failures ({len(failures)}):")
        for paper, err in failures:
            print(f"  - {paper}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
