#!/usr/bin/env python3
"""Extract agentic concern sheets from review output directories.

Mechanically parses review.md and summary.yaml to produce YAML files
conforming to the AgenticConcernSheet schema (v1).

Usage:
    # Single result directory
    python scripts/extract_agentic_concerns_batch.py \\
        --result-dir <review_run_dir>/<paper_slug> \\
        --output data/agentic_concerns/<version>/<method>/<paper_slug>.yaml

    # Batch from file (one result-dir per line)
    python scripts/extract_agentic_concerns_batch.py --batch-file batch.txt

    # Auto-discover all method conditions
    python scripts/extract_agentic_concerns_batch.py --all-conditions
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_VERSION = "v1"
DEFAULT_VERSION = "skill_injection_validation"

# Keyword -> tag mapping for heuristic tag generation
TAG_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"variance|seed|confidence interval|error bar|standard deviation", re.I), "missing_statistics"),
    (re.compile(r"novelty|delta|incremental|engineering extension", re.I), "limited_novelty"),
    (re.compile(r"baseline|comparison|fairness", re.I), "baseline_fairness"),
    (re.compile(r"confound|leakage|circular", re.I), "confounding"),
    (re.compile(r"ablation", re.I), "incomplete_ablation"),
    (re.compile(r"reproduci", re.I), "reproducibility"),
    (re.compile(r"robustness|generali[sz]", re.I), "generalization"),
    (re.compile(r"clarity|writing|fluff", re.I), "clarity"),
    (re.compile(r"defense|defen[cs]e evaluation", re.I), "narrow_evaluation"),
    (re.compile(r"cherry.?pick|selective reporting", re.I), "cherry_picking"),
    (re.compile(r"scale|scaling", re.I), "limited_scale"),
    (re.compile(r"hyperparameter|sensitivity", re.I), "missing_sensitivity"),
    (re.compile(r"failure mode|when.*fail", re.I), "missing_failure_analysis"),
    (re.compile(r"judge|evaluator|metric validity", re.I), "evaluation_validity"),
    (re.compile(r"code.*release|artifact|open.?source", re.I), "code_availability"),
    (re.compile(r"single benchmark|narrow.*evaluation|one.*dataset", re.I), "narrow_evaluation"),
    (re.compile(r"overstated|overclaim|misleading", re.I), "overclaiming"),
    (re.compile(r"retrieval|state.?tracking", re.I), "capability_limitation"),
]

# Keyword -> dimension mapping
DIMENSION_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"problem|motivation", re.I), "A"),
    (re.compile(r"novelty|delta|incremental|insight", re.I), "B"),
    (re.compile(r"technical quality|method design", re.I), "C"),
    (re.compile(r"baseline|evaluation|statistical|judge|variance|confound|defense|benchmark", re.I), "D"),
    (re.compile(r"ablation|causal|mechanism|component", re.I), "E"),
    (re.compile(r"robustness|generali[sz]|scale|failure mode", re.I), "F"),
    (re.compile(r"clarity|writing|disclosure|transparency|fluff|overstated|misleading", re.I), "G"),
    (re.compile(r"reproduci|code|artifact", re.I), "H"),
]

# Gate name -> dimension mapping
GATE_DIMENSION_MAP = {
    "G0": "A",
    "G1": "D",
    "G2": "D",
    "G3": "H",
    "G4": "D",
    "G5": "B",
    "G6": "D",
    "G7": "G",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Concern:
    id: str
    text: str
    severity_level: str
    severity_addressability: str
    severity_mechanism: str
    source: str
    source_detail: str
    decisive: bool
    tags: list[str]
    dimension_impact: list[str]
    origin: str | None = None
    origin_pointer: str | None = None


@dataclass
class DecisionDriver:
    id: str
    polarity: str
    text: str
    evidence: str
    linked_concern_ids: list[str]


@dataclass
class Mention:
    id: str
    polarity: str
    text: str
    evidence: str
    note: str


@dataclass
class ExtractionResult:
    paper_slug: str
    method: str
    verdict: str
    score: float | None
    decision_drivers: list[DecisionDriver]
    mentions: list[Mention]
    concerns: list[Concern]
    method_specific: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning empty dict on failure."""
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning("Failed to load %s: %s", path, e)
        return {}


def load_text_file(path: Path) -> str:
    """Load a text file, returning empty string on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to load %s: %s", path, e)
        return ""


def infer_tags(text: str) -> list[str]:
    """Generate tags from concern text using keyword heuristics."""
    tags = []
    for pattern, tag in TAG_PATTERNS:
        if pattern.search(text):
            tags.append(tag)
    return list(dict.fromkeys(tags))  # deduplicate preserving order


def infer_dimensions(text: str) -> list[str]:
    """Infer scorecard dimension impact from concern text."""
    dims = set()
    for pattern, dim in DIMENSION_PATTERNS:
        if pattern.search(text):
            dims.add(dim)
    return sorted(dims)


def parse_severity_label(label: str) -> tuple[str, str]:
    """Parse severity label from parenthetical.

    Returns (level, addressability).
    Handles multi-word labels like "addressable but significant".
    """
    label = label.strip().lower()
    mapping = {
        "fatal": ("fatal", "unresolved"),
        "unknown": ("major", "unknown"),
        "addressable": ("major", "addressable"),
        "unresolved": ("major", "unresolved"),
        "moderate": ("moderate", "unknown"),
    }
    if label in mapping:
        return mapping[label]
    # Handle compound labels: "addressable but significant", etc.
    if "fatal" in label:
        return ("fatal", "unresolved")
    if "addressable" in label:
        return ("major", "addressable")
    if "unresolved" in label:
        return ("major", "unresolved")
    return ("major", "unknown")


def parse_origin_info(text: str) -> tuple[str | None, str | None]:
    """Parse origin and origin_pointer from concern text.

    Handles formats like:
    - "Origin: skeptic | Origin pointer: skeptic bullet #1"
    - "Origin: skeptic"
    - "Origin: skeptic (refuted by calibrator, but retained at CAUTION level)"
    - "(Origin: calibrator)"
    - "— Origin: X, pointer Y"
    """
    origin = None
    origin_pointer = None

    # Multi-line or inline format: "- Origin: X | Origin pointer: Y"
    # Also handles bold variant: "- **Origin**: X | **Origin pointer**: Y"
    # Be careful to stop at newline or pipe for the origin value
    m = re.search(
        r"(?:^|\n)\s*-?\s*\*{0,2}Origin\*{0,2}:\s*([^|\n]+?)(?:\s*\|\s*\*{0,2}Origin\s*pointer\*{0,2}:\s*([^\n]+?))?(?:\n|$)",
        text,
    )
    if m:
        raw_origin = m.group(1).strip()
        # Clean parenthetical notes from origin value
        # e.g., "skeptic (refuted by calibrator...)" → "skeptic"
        clean = re.match(r"^(\w+(?:\s*/\s*\w+)?)", raw_origin)
        if clean:
            origin = clean.group(1).strip()
        else:
            origin = raw_origin.rstrip(")")
        if m.group(2):
            origin_pointer = m.group(2).strip().rstrip(")")

    # Also handle "— Origin: X" inline format for minor concerns
    # Stop at parenthetical notes: "Origin: champion (acknowledged weakness)"
    if origin is None:
        m = re.search(r"[—–-]\s*Origin:\s*([^,\n()]+?)(?:\s*[,()}\n]|$)", text)
        if m:
            raw = m.group(1).strip()
            # If the raw value contains multiple words, split origin from pointer
            # e.g., "skeptic bullet #2" → origin="skeptic", pointer="bullet #2"
            # Known origin names that may be followed by a pointer
            known_origins = {"skeptic", "champion", "calibrator", "gates", "scorecard", "adversarial"}
            first_word = raw.split()[0].lower() if raw else ""
            if first_word in known_origins and len(raw.split()) > 1:
                origin = raw.split()[0]
                origin_pointer = " ".join(raw.split()[1:])
            else:
                origin = raw
            # Check for origin_pointer in the parenthetical
            ptr_m = re.search(r"[—–-]\s*Origin:\s*[^(]+\(([^)]+)\)", text)
            if ptr_m:
                origin_pointer = ptr_m.group(1).strip()

    # Handle parenthetical at end: "(Origin: X, pointer Y)"
    if origin is None:
        m = re.search(r"\(Origin:\s*([^,)]+?)(?:,\s*(.+?))?\)", text)
        if m:
            origin = m.group(1).strip()
            if m.group(2):
                origin_pointer = m.group(2).strip()

    # Final cleanup: strip trailing punctuation and whitespace
    if origin:
        origin = origin.rstrip(" .,;:")
    if origin_pointer:
        origin_pointer = origin_pointer.rstrip(" .,;:")

    return origin, origin_pointer


def is_gate_concern(text: str) -> tuple[bool, str]:
    """Check if concern is gate-related. Returns (is_gate, mechanism)."""
    if re.search(r"\bG\d\b.*(?:FAIL|fail)", text):
        return True, "gate_fail"
    if re.search(r"\bG\d\b.*(?:CAUTION|caution)", text):
        return True, "gate_caution"
    if re.search(r"(?:CAUTION|caution).*\bG\d\b", text):
        return True, "gate_caution"
    if re.search(r"gate.*(?:FAIL|fail)", text, re.I):
        return True, "gate_fail"
    if re.search(r"gate.*(?:CAUTION|caution)", text, re.I):
        return True, "gate_caution"
    return False, "none"


def gate_dim_from_text(text: str) -> list[str]:
    """Extract gate dimensions from concern text (e.g., G4 -> D)."""
    dims = set()
    for m in re.finditer(r"\bG(\d)\b", text):
        gate = f"G{m.group(1)}"
        if gate in GATE_DIMENSION_MAP:
            dims.add(GATE_DIMENSION_MAP[gate])
    return sorted(dims)


# ---------------------------------------------------------------------------
# Major concern parsing
# ---------------------------------------------------------------------------

def split_major_concerns(review_text: str) -> list[str]:
    """Split the major concerns section into individual concern blocks."""
    # Find the major concerns section
    m = re.search(
        r"##\s*Major\s+concerns.*?\n(.*?)(?=\n##\s|\Z)",
        review_text,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return []

    section = m.group(1)

    # Split on numbered items: "1. **" or "### 1." or "### 1. **"
    # Handle both "1. **Title" and "### 1. Title" formats
    blocks = re.split(r"\n(?=(?:\d+\.\s+\*\*|###\s+\d+\.\s))", section)
    return [b.strip() for b in blocks if b.strip()]


def parse_one_major(block: str, idx: int) -> Concern | None:
    """Parse a single major concern block into a Concern."""
    # Extract title and severity label
    # Format 1: "1. **Title text (severity_label)**"
    # Format 2: "### 1. Title text **(severity_label)**"
    # Format 3: "1. **Title text** (severity_label)"
    # Format 4: "### 1. Title text (severity_label)"

    title_text = ""
    severity_label = "unknown"

    # Try: "**Title (label)**"
    m = re.search(r"\*\*(.+?)\s*\((\w+)\)\s*\*\*", block)
    if m:
        title_text = m.group(1).strip()
        severity_label = m.group(2).strip()
    else:
        # Try: "**Title** (label)"  or "**Title text** **(label)**"
        m = re.search(r"\*\*(.+?)\*\*\s*(?:\*\*)?\((\w+)\)(?:\*\*)?", block)
        if m:
            title_text = m.group(1).strip()
            severity_label = m.group(2).strip()
        else:
            # Try: "### N. Title **(label)**"
            m = re.search(r"###\s*\d+\.\s*(.+?)\s*\*\*\((\w+)\)\*\*", block)
            if m:
                title_text = m.group(1).strip()
                severity_label = m.group(2).strip()
            else:
                # Try: "### N. Title (label)" — no bold, plain text with parens
                m = re.search(r"###\s*\d+\.\s*(.+?)\s*\(([^)]+)\)\s*$", block, re.MULTILINE)
                if m:
                    title_text = m.group(1).strip()
                    severity_label = m.group(2).strip()
                else:
                    # Just get the bold title without severity
                    m = re.search(r"\*\*(.+?)\*\*", block)
                    if m:
                        title_text = m.group(1).strip()
                        # Check for severity in parenthetical after the bold
                        sev_m = re.search(r"\*\*\s*\((\w+)\)", block)
                        if sev_m:
                            severity_label = sev_m.group(1).strip()
                    else:
                        # Last resort: "### N. Title" or "N. Title" with no severity
                        m = re.search(r"(?:###\s*)?\d+\.\s*(.+?)(?:\n|$)", block)
                        if m:
                            title_text = m.group(1).strip()

    if not title_text:
        logger.warning("Could not parse major concern title from block: %.100s...", block)
        return None

    level, addressability = parse_severity_label(severity_label)
    origin, origin_pointer = parse_origin_info(block)

    # Determine mechanism
    is_gate, gate_mechanism = is_gate_concern(block)
    mechanism = gate_mechanism if is_gate else "none"

    # Determine source
    if is_gate:
        source = "gates"
    else:
        source = "review_major"

    # Build source_detail from evidence/location lines
    source_detail_parts = []
    for line in block.split("\n"):
        line_stripped = line.strip().lstrip("- ")
        if re.match(r"(?:Evidence|Evidence location):", line_stripped, re.I):
            source_detail_parts.append(line_stripped)
        elif re.match(r"Origin pointer:", line_stripped, re.I):
            source_detail_parts.append(line_stripped)
    source_detail = "; ".join(source_detail_parts) if source_detail_parts else f"Review major concern #{idx + 1}"

    # Extract "Why it matters" text for richer tag/dimension inference
    why_match = re.search(r"Why it matters:\s*(.+?)(?=\n\s*-|\n\s*$|\Z)", block, re.DOTALL)
    why_text = why_match.group(1).strip() if why_match else ""

    # Tags: use title + why-it-matters (not full block to avoid noise from
    # evidence locations and concrete fixes)
    tag_context = title_text + " " + why_text
    tags = infer_tags(tag_context)
    if is_gate:
        if "gate_caution" not in tags and mechanism == "gate_caution":
            tags.append("gate_caution")
        if "gate_fail" not in tags and mechanism == "gate_fail":
            tags.append("gate_fail")

    # Dimension impact: use title + why-it-matters + gate info
    dim_context = title_text + " " + why_text
    dims = infer_dimensions(dim_context)
    if is_gate:
        gate_dims = gate_dim_from_text(block)
        dims = sorted(set(dims) | set(gate_dims))

    return Concern(
        id=f"A{idx + 1}",
        text=title_text,
        severity_level=level,
        severity_addressability=addressability,
        severity_mechanism=mechanism,
        source=source,
        source_detail=source_detail,
        decisive=False,  # Will be set later based on decision_drivers
        tags=tags,
        dimension_impact=dims,
        origin=origin,
        origin_pointer=origin_pointer,
    )


# ---------------------------------------------------------------------------
# Minor concern parsing
# ---------------------------------------------------------------------------

def split_minor_concerns(review_text: str) -> list[str]:
    """Split the minor concerns section into individual concern lines."""
    m = re.search(
        r"##\s*Minor\s+concerns.*?\n(.*?)(?=\n##\s|\Z)",
        review_text,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return []

    section = m.group(1)

    # Split on numbered items: "1. **" or "1. " (for non-bold format)
    blocks = re.split(r"\n(?=\d+\.\s+)", section)
    return [b.strip() for b in blocks if b.strip()]


def parse_one_minor(block: str, idx: int, major_count: int) -> Concern | None:
    """Parse a single minor concern block."""
    # Extract the bold title
    m = re.search(r"\*\*(.+?)\*\*", block)
    if m:
        title_text = m.group(1).strip()
    else:
        # No bold — extract the first sentence as title
        m = re.search(r"\d+\.\s+(.+?)(?:[.—–]|\s*\(Origin)", block)
        if not m:
            logger.warning("Could not parse minor concern from: %.100s...", block)
            return None
        title_text = m.group(1).strip().rstrip(".")

    # Get the rest as description
    # Minor concerns are typically one line/paragraph
    origin, origin_pointer = parse_origin_info(block)

    # Check for gate mentions
    is_gate, gate_mechanism = is_gate_concern(block)
    mechanism = gate_mechanism if is_gate else "none"
    source = "gates" if is_gate else "review_minor"

    tags = infer_tags(title_text + " " + block)
    dims = infer_dimensions(title_text + " " + block)
    if is_gate:
        gate_dims = gate_dim_from_text(block)
        dims = sorted(set(dims) | set(gate_dims))

    concern_id = f"A{major_count + idx + 1}"
    source_detail = f"Review minor concern #{idx + 1}"

    return Concern(
        id=concern_id,
        text=title_text,
        severity_level="minor",
        severity_addressability="addressable",
        severity_mechanism=mechanism,
        source=source,
        source_detail=source_detail,
        decisive=False,
        tags=tags,
        dimension_impact=dims,
        origin=origin,
        origin_pointer=origin_pointer,
    )


# ---------------------------------------------------------------------------
# Decision driver parsing
# ---------------------------------------------------------------------------

def parse_decisive_reasons(
    summary: dict[str, Any],
    review_text: str,
    verdict: str,
) -> list[DecisionDriver]:
    """Parse decisive reasons from summary.yaml into DecisionDrivers."""
    reasons = summary.get("decisive_reasons", [])
    if not reasons:
        # Fallback: try parsing from review.md
        m = re.search(
            r"Decisive reasons:\s*\n((?:\s+\d+\..*\n?)+)",
            review_text,
        )
        if m:
            reason_block = m.group(1)
            reasons = re.findall(r"\d+\.\s+(.+?)(?=\n\s+\d+\.|\Z)", reason_block, re.DOTALL)
            reasons = [r.strip() for r in reasons]

    polarity = "pro_reject" if verdict == "REJECT" else "pro_accept"
    drivers = []
    for i, reason in enumerate(reasons):
        # Clean up YAML multiline artifacts
        reason_text = re.sub(r"\s+", " ", str(reason)).strip()
        drivers.append(DecisionDriver(
            id=f"R{i + 1}",
            polarity=polarity,
            text=reason_text,
            evidence=f"summary.yaml decisive_reasons[{i}]",
            linked_concern_ids=[],  # Will be linked after concern parsing
        ))

    return drivers


# ---------------------------------------------------------------------------
# Mention parsing (from panel resolution and one-paragraph summary)
# ---------------------------------------------------------------------------

def parse_mentions(
    review_text: str,
    summary: dict[str, Any],
    verdict: str,
) -> list[Mention]:
    """Extract mentions from review text.

    For REJECT verdicts, pro_accept mentions come from:
    - Champion's above-the-line / acknowledged strengths
    - Panel resolution positive points
    - One-paragraph summary positive aspects

    For ACCEPT verdicts, pro_reject mentions come from:
    - Skeptic's decisive point
    - Champion's acknowledged weakness
    """
    mentions: list[Mention] = []
    mention_idx = 1

    panel = summary.get("panel", {})

    if verdict == "REJECT":
        # Extract champion's above-the-line as a mention
        champion_atl = panel.get("champion_above_the_line", "")
        if champion_atl:
            mentions.append(Mention(
                id=f"M{mention_idx}",
                polarity="pro_accept",
                text=str(champion_atl).strip(),
                evidence="summary.yaml panel.champion_above_the_line",
                note="Champion's strongest argument; calibrator ruled insufficient to overcome decisive concerns.",
            ))
            mention_idx += 1

    elif verdict == "ACCEPT":
        # Extract skeptic's decisive point as a mention
        skeptic_point = panel.get("skeptic_decisive_point", "")
        if skeptic_point:
            mentions.append(Mention(
                id=f"M{mention_idx}",
                polarity="pro_reject",
                text=str(skeptic_point).strip(),
                evidence="summary.yaml panel.skeptic_decisive_point",
                note="Skeptic's strongest argument; calibrator refuted or ruled non-fatal.",
            ))
            mention_idx += 1

    # Extract champion's acknowledged weakness (always a pro_reject mention)
    champion_weakness = _extract_champion_weakness(review_text)
    if champion_weakness:
        mentions.append(Mention(
            id=f"M{mention_idx}",
            polarity="pro_reject" if verdict == "ACCEPT" else "pro_reject",
            text=champion_weakness,
            evidence="review.md panel resolution, champion's acknowledged weakness",
            note="Acknowledged weakness; not treated as decisive.",
        ))
        mention_idx += 1

    return mentions


def _extract_champion_weakness(review_text: str) -> str | None:
    """Extract champion's acknowledged weakness from panel resolution."""
    m = re.search(
        r"[Cc]hampion's\s+acknowledged\s+weakness[:\s]*(.+?)(?=\n-\s|\n##|\n\n|\Z)",
        review_text,
    )
    if m:
        text = m.group(1).strip()
        # Remove leading "**" formatting and leading punctuation
        text = re.sub(r"^\*\*|\*\*$", "", text).strip()
        text = re.sub(r"^[:\s]+", "", text).strip()
        return text if text else None
    return None


# ---------------------------------------------------------------------------
# Link decision drivers to concerns
# ---------------------------------------------------------------------------

def link_drivers_to_concerns(
    drivers: list[DecisionDriver],
    concerns: list[Concern],
) -> None:
    """Link decision drivers to concerns by text similarity and mark decisive.

    Uses longer words (5+ chars) and requires higher overlap to avoid false
    positives from common short words like "over", "does", "from", etc.
    """
    # Common words that should not contribute to matching
    stop_words = {
        "about", "above", "access", "across", "after", "against", "along",
        "among", "analysis", "around", "based", "before", "being", "below",
        "between", "beyond", "calibrator", "cannot", "claims", "contribution",
        "could", "despite", "doing", "during", "error", "every", "experiment",
        "experiments", "first", "gains", "given", "having", "however",
        "improvement", "improvements", "large", "level", "limited", "makes",
        "margin", "margins", "might", "model", "models", "number", "only",
        "other", "paper", "point", "points", "primary", "providing", "rather",
        "report", "reported", "results", "running", "score",
        "setting", "settings", "should", "shows", "since", "single", "small",
        "specific", "still", "table", "their", "there", "these", "those",
        "three", "total", "under", "until", "using", "which", "while",
        "within", "without", "would",
    }

    for driver in drivers:
        driver_text = driver.text.lower()
        best_matches: list[str] = []

        for concern in concerns:
            concern_title = concern.text.lower()
            # Use 5+ char words from concern title only (not full block)
            # to match against the driver text
            driver_words = set(re.findall(r"\w{5,}", driver_text)) - stop_words
            concern_words = set(re.findall(r"\w{5,}", concern_title)) - stop_words
            overlap = driver_words & concern_words

            # Require at least 2 significant word overlaps, OR 1 overlap if the
            # concern title is very short (3 words or fewer)
            title_word_count = len(concern_title.split())
            threshold = 1 if title_word_count <= 3 else 2

            if len(overlap) >= threshold:
                best_matches.append(concern.id)
                concern.decisive = True

        driver.linked_concern_ids = best_matches


# ---------------------------------------------------------------------------
# Method-specific metadata
# ---------------------------------------------------------------------------

def extract_method_specific(
    summary: dict[str, Any],
    review_text: str,
) -> dict[str, Any]:
    """Extract method-specific metadata."""
    method = summary.get("method", "")
    meta: dict[str, Any] = {}

    if method == "panel":
        panel = summary.get("panel", {})
        meta["panel_structure"] = "champion-skeptic-calibrator"

        resolution = panel.get("calibrator_resolution", "")
        meta["calibrator_resolution"] = str(resolution)

        # Extract verdicts from review text
        if panel.get("skeptic_decisive_point"):
            meta["skeptic_decisive_point"] = str(panel["skeptic_decisive_point"])
        if panel.get("champion_above_the_line"):
            meta["champion_above_the_line"] = str(panel["champion_above_the_line"])

        # Score floor info
        score_floor = (summary.get("scorecard") or {}).get("score_floor_status", "")
        if score_floor and str(score_floor).upper() not in ("N/A", "PASS", "NONE", "NULL"):
            meta["score_floor_status"] = str(score_floor)

    return meta


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def extract_from_directory(result_dir: Path) -> ExtractionResult:
    """Extract an agentic concern sheet from a result directory."""
    warnings: list[str] = []

    # Load inputs
    summary = load_yaml_file(result_dir / "summary.yaml")
    review_text = load_text_file(result_dir / "review.md")

    if not summary:
        warnings.append(f"Missing or empty summary.yaml in {result_dir}")
    if not review_text:
        warnings.append(f"Missing or empty review.md in {result_dir}")

    # Core fields
    paper_slug = summary.get("paper_slug", result_dir.name)
    method = summary.get("method", "panel")
    verdict = summary.get("verdict", "REJECT")
    scorecard = summary.get("scorecard") or {}
    score = scorecard.get("total")
    if score is not None:
        try:
            score = float(score)
        except (TypeError, ValueError):
            warnings.append(f"Could not parse scorecard total: {score}")
            score = None

    # Parse major concerns
    major_blocks = split_major_concerns(review_text)
    major_concerns: list[Concern] = []
    for i, block in enumerate(major_blocks):
        c = parse_one_major(block, i)
        if c:
            major_concerns.append(c)

    if not major_concerns and review_text:
        warnings.append("No major concerns found in review.md")

    # Parse minor concerns
    minor_blocks = split_minor_concerns(review_text)
    minor_concerns: list[Concern] = []
    for i, block in enumerate(minor_blocks):
        c = parse_one_minor(block, i, len(major_concerns))
        if c:
            minor_concerns.append(c)

    all_concerns = major_concerns + minor_concerns

    # Add gate concerns if they aren't already captured in majors/minors
    gates = summary.get("gates", {})
    existing_gate_mentions = {c.text for c in all_concerns if c.source == "gates"}
    for gate_key, gate_val in gates.items():
        val_str = str(gate_val).upper()
        if val_str in ("CAUTION", "FAIL"):
            gate_name = gate_key.split("_")[0].upper()  # e.g. "G4"
            # Check if this gate is already covered
            gate_already_covered = any(
                gate_name in c.text or gate_name in c.source_detail
                for c in all_concerns
            )
            if not gate_already_covered:
                gate_idx = len(all_concerns)
                dim = GATE_DIMENSION_MAP.get(gate_name, "D")
                mechanism = "gate_fail" if val_str == "FAIL" else "gate_caution"
                level = "fatal" if val_str == "FAIL" else "major"
                all_concerns.append(Concern(
                    id=f"A{gate_idx + 1}",
                    text=f"Gate {gate_name} = {val_str}",
                    severity_level=level,
                    severity_addressability="addressable" if val_str == "CAUTION" else "unresolved",
                    severity_mechanism=mechanism,
                    source="gates",
                    source_detail=f"gates.md {gate_name}={val_str}",
                    decisive=val_str == "FAIL",
                    tags=["gate_caution" if val_str == "CAUTION" else "gate_fail"],
                    dimension_impact=[dim],
                    origin="gates",
                    origin_pointer=f"gates {gate_name}",
                ))

    # Parse decision drivers
    drivers = parse_decisive_reasons(summary, review_text, verdict)

    # Parse mentions
    mentions = parse_mentions(review_text, summary, verdict)

    # Link drivers to concerns
    link_drivers_to_concerns(drivers, all_concerns)

    # Method-specific metadata
    method_specific = extract_method_specific(summary, review_text)

    return ExtractionResult(
        paper_slug=paper_slug,
        method=method,
        verdict=verdict,
        score=score,
        decision_drivers=drivers,
        mentions=mentions,
        concerns=all_concerns,
        method_specific=method_specific,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# YAML output
# ---------------------------------------------------------------------------

def result_to_dict(result: ExtractionResult, version: str = DEFAULT_VERSION) -> dict[str, Any]:
    """Convert ExtractionResult to a schema-conformant dict for YAML output."""
    out: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "paper": result.paper_slug,
        "version": version,
        "method": result.method,
        "verdict": result.verdict,
        "score": result.score,
    }

    # Decision drivers
    out["decision_drivers"] = [
        _strip_none({
            "id": d.id,
            "polarity": d.polarity,
            "text": d.text,
            "evidence": d.evidence,
            "linked_concern_ids": d.linked_concern_ids or [],
        })
        for d in result.decision_drivers
    ]

    # Mentions
    out["mentions"] = [
        _strip_none({
            "id": m.id,
            "polarity": m.polarity,
            "text": m.text,
            "evidence": m.evidence,
            "note": m.note,
        })
        for m in result.mentions
    ]

    # Concerns
    out["concerns"] = []
    for c in result.concerns:
        concern_dict: dict[str, Any] = {
            "id": c.id,
            "text": c.text,
            "severity": {
                "level": c.severity_level,
                "addressability": c.severity_addressability,
                "mechanism": c.severity_mechanism,
            },
            "source": c.source,
            "source_detail": c.source_detail,
            "decisive": c.decisive,
            "tags": c.tags,
            "dimension_impact": c.dimension_impact,
        }
        if c.origin:
            concern_dict["origin"] = c.origin
        if c.origin_pointer:
            concern_dict["origin_pointer"] = c.origin_pointer
        out["concerns"].append(concern_dict)

    # Method-specific
    if result.method_specific:
        out["method_specific"] = result.method_specific

    return out


def _strip_none(d: dict) -> dict:
    """Remove keys with None values."""
    return {k: v for k, v in d.items() if v is not None}


class YamlDumper(yaml.SafeDumper):
    """Custom YAML dumper for readable output."""
    pass


def _str_representer(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    """Use literal block style for multiline strings, otherwise default."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    if len(data) > 120:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


YamlDumper.add_representer(str, _str_representer)


def write_yaml(data: dict[str, Any], output_path: Path) -> None:
    """Write data to YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            Dumper=YamlDumper,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )
    logger.info("Wrote %s", output_path)


# ---------------------------------------------------------------------------
# Auto-discovery for --all-conditions
# ---------------------------------------------------------------------------

ALL_SLUGS_S1 = ["tool_tree", "openapps", "honesty_alignment", "rl_obfuscation"]
ALL_SLUGS_S2 = [
    "adversarial_rl", "safedpo", "adversarial_dejavu",
    "eigenbench", "mamba3", "graf_jailbreak",
]
ALL_SLUGS = ALL_SLUGS_S1 + ALL_SLUGS_S2


@dataclass
class DiscoveredRun:
    result_dir: Path
    output_path: Path
    condition: str
    slug: str


def discover_all_conditions() -> list[DiscoveredRun]:
    """Auto-discover all validation runs across conditions A-D."""
    cal_root = REPO_ROOT / "calibration" / "results"
    out_root = REPO_ROOT / "calibration" / "concern_alignment" / "agentic" / DEFAULT_VERSION

    runs: list[DiscoveredRun] = []

    # --- Condition A ---
    # S1 papers: lit_search_validation/{slug}/condition_a/
    for slug in ALL_SLUGS_S1:
        d = cal_root / "lit_search_validation" / slug / "condition_a"
        if d.is_dir() and (d / "summary.yaml").exists():
            runs.append(DiscoveredRun(
                result_dir=d,
                output_path=out_root / "cond_a" / f"{slug}.yaml",
                condition="a",
                slug=slug,
            ))

    # S2 papers: lit_search_validation_condA/{slug}/
    for slug in ALL_SLUGS_S2:
        d = cal_root / "lit_search_validation_condA" / slug
        if d.is_dir() and (d / "summary.yaml").exists():
            runs.append(DiscoveredRun(
                result_dir=d,
                output_path=out_root / "cond_a" / f"{slug}.yaml",
                condition="a",
                slug=slug,
            ))

    # Also check S2 papers under lit_search_validation/{slug}/condition_a/
    for slug in ALL_SLUGS_S2:
        d = cal_root / "lit_search_validation" / slug / "condition_a"
        if d.is_dir() and (d / "summary.yaml").exists():
            # Only add if not already discovered via condA path
            existing = {r.slug for r in runs if r.condition == "a"}
            if slug not in existing:
                runs.append(DiscoveredRun(
                    result_dir=d,
                    output_path=out_root / "cond_a" / f"{slug}.yaml",
                    condition="a",
                    slug=slug,
                ))

    # --- Condition B ---
    for slug in ALL_SLUGS_S1:
        d = cal_root / "lit_search_validation" / slug / "condition_b"
        if d.is_dir() and (d / "summary.yaml").exists():
            runs.append(DiscoveredRun(
                result_dir=d,
                output_path=out_root / "cond_b" / f"{slug}.yaml",
                condition="b",
                slug=slug,
            ))

    for slug in ALL_SLUGS_S2:
        d = cal_root / "lit_search_validation_condB" / slug
        if d.is_dir() and (d / "summary.yaml").exists():
            runs.append(DiscoveredRun(
                result_dir=d,
                output_path=out_root / "cond_b" / f"{slug}.yaml",
                condition="b",
                slug=slug,
            ))

    for slug in ALL_SLUGS_S2:
        d = cal_root / "lit_search_validation" / slug / "condition_b"
        if d.is_dir() and (d / "summary.yaml").exists():
            existing = {r.slug for r in runs if r.condition == "b"}
            if slug not in existing:
                runs.append(DiscoveredRun(
                    result_dir=d,
                    output_path=out_root / "cond_b" / f"{slug}.yaml",
                    condition="b",
                    slug=slug,
                ))

    # --- Condition C ---
    for slug in ALL_SLUGS:
        d = cal_root / "lit_search_validation_condC" / slug
        if d.is_dir() and (d / "summary.yaml").exists():
            runs.append(DiscoveredRun(
                result_dir=d,
                output_path=out_root / "cond_c" / f"{slug}.yaml",
                condition="c",
                slug=slug,
            ))

    for slug in ALL_SLUGS:
        d = cal_root / "lit_search_validation" / slug / "condition_c"
        if d.is_dir() and (d / "summary.yaml").exists():
            existing = {r.slug for r in runs if r.condition == "c"}
            if slug not in existing:
                runs.append(DiscoveredRun(
                    result_dir=d,
                    output_path=out_root / "cond_c" / f"{slug}.yaml",
                    condition="c",
                    slug=slug,
                ))

    # --- Condition D ---
    for slug in ALL_SLUGS:
        d = cal_root / "lit_search_validation_condD" / slug
        if d.is_dir() and (d / "summary.yaml").exists():
            runs.append(DiscoveredRun(
                result_dir=d,
                output_path=out_root / "cond_d" / f"{slug}.yaml",
                condition="d",
                slug=slug,
            ))

    return runs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def process_single(
    result_dir: Path,
    output_path: Path,
    version: str = DEFAULT_VERSION,
) -> ExtractionResult:
    """Process a single result directory and write output."""
    result = extract_from_directory(result_dir)
    data = result_to_dict(result, version=version)
    write_yaml(data, output_path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract agentic concern sheets from review output directories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--result-dir",
        type=Path,
        help="Single result directory to process.",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output YAML path (required with --result-dir).",
    )
    parser.add_argument(
        "--batch-file",
        type=Path,
        help="File with one result-dir per line.",
    )
    parser.add_argument(
        "--all-conditions",
        action="store_true",
        help="Auto-discover all validation runs across conditions A-D.",
    )
    parser.add_argument(
        "--version",
        default=DEFAULT_VERSION,
        help=f"Version string for the concern sheet (default: {DEFAULT_VERSION}).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Validate arguments
    if not any([args.result_dir, args.batch_file, args.all_conditions]):
        parser.error("One of --result-dir, --batch-file, or --all-conditions is required.")

    if args.result_dir and not args.output:
        parser.error("--output is required when using --result-dir.")

    # Collect jobs
    jobs: list[tuple[Path, Path]] = []

    if args.result_dir:
        jobs.append((args.result_dir.resolve(), args.output.resolve()))

    elif args.batch_file:
        if not args.batch_file.exists():
            logger.error("Batch file not found: %s", args.batch_file)
            sys.exit(1)

        out_root = REPO_ROOT / "calibration" / "concern_alignment" / "agentic" / args.version
        for line in args.batch_file.read_text().strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("\t")
            result_dir = Path(parts[0]).resolve()
            if len(parts) > 1:
                output_path = Path(parts[1]).resolve()
            else:
                # Auto-generate output path from result_dir slug
                slug = result_dir.name
                if slug in ("condition_a", "condition_b", "condition_c", "condition_d",
                             "with", "without"):
                    slug = result_dir.parent.name
                output_path = out_root / f"{slug}.yaml"

            jobs.append((result_dir, output_path))

    elif args.all_conditions:
        discovered = discover_all_conditions()
        logger.info("Discovered %d validation runs.", len(discovered))
        for run in discovered:
            jobs.append((run.result_dir, run.output_path))

    # Process jobs
    summary_stats: dict[str, int] = {}
    total_concerns = 0
    total_warnings = 0
    errors = 0

    for result_dir, output_path in jobs:
        label = str(result_dir.relative_to(REPO_ROOT)) if result_dir.is_relative_to(REPO_ROOT) else str(result_dir)
        try:
            result = process_single(result_dir, output_path, version=args.version)
            n_concerns = len(result.concerns)
            total_concerns += n_concerns
            total_warnings += len(result.warnings)
            summary_stats[label] = n_concerns

            for w in result.warnings:
                logger.warning("[%s] %s", label, w)

        except Exception as e:
            logger.error("[%s] Failed: %s", label, e)
            errors += 1

    # Print summary
    print("\n" + "=" * 70)
    print("EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"Total runs processed: {len(jobs)}")
    print(f"Total concerns extracted: {total_concerns}")
    print(f"Total warnings: {total_warnings}")
    print(f"Errors: {errors}")
    print("-" * 70)
    print(f"{'Directory':<55} {'Concerns':>8}")
    print("-" * 70)
    for label, count in sorted(summary_stats.items()):
        # Truncate long paths for display
        display = label if len(label) <= 55 else "..." + label[-(55 - 3):]
        print(f"{display:<55} {count:>8}")
    print("=" * 70)

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
