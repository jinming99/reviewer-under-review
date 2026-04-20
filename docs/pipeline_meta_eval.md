# Meta-Evaluation Pipeline: Concern Alignment

## Purpose

Evaluate AI-generated paper reviews by comparing them against official OpenReview reviews. The pipeline measures **what** concerns the system raises, **how** severely it weights them, and **where** its priorities diverge from the rationale that drove the venue decision. It produces per-paper match graphs and per-system L0–L4 metrics.

This doc describes the pipeline at the level needed to read the output artifacts or reproduce the benchmark. For the full framework including worked examples, see [`concern_alignment_evaluation.md`](concern_alignment_evaluation.md). For per-step prompting details, use the Claude Code skills under `.claude/skills/` in this repository.

## Prerequisites

- OpenReview threads available for each paper (reviews, rebuttal, meta-review).
- AI review outputs for each paper × system configuration, in the project's review layout (`data/reviews/public_slice/<system>_<model>_run<N>/<paper_slug>/review.md`).
- Ground truth decisions and paper metadata in `data/ground_truth.yaml`.
- Each produced artifact validates against the schemas in `schemas/` (reference validator: `scripts/lint_concern_alignment.py`).

## Pipeline

### Step 1 — Extract official concern sheet

Input: official review text + paper PDF for one paper.
Output: `data/official_concerns/<calibration_set>/<paper_slug>.yaml` — one structured concern sheet per paper, shared across all system configurations.

Each concern carries: atomic description, severity (fatal / major / moderate / minor), AC treatment (`decisive_blocker`, `unresolved`, `resolved`, `accepted_limitation`), resolution status after rebuttal, and topic tags.

The project skill for this step is `.claude/skills/skill-1-official-concern-extraction/SKILL.md`. Schema: `schemas/official_concern_sheet.schema.yaml`.

### Step 2 — Extract agentic concern sheet

Input: one AI review output for one paper × system configuration.
Output: `data/agentic_concerns/public_slice/<system_dir>/<paper_slug>.yaml`.

Each agentic concern carries: text, severity (with `level`, `addressability`, optional `mechanism`), source (review major/minor/gates/etc.), decisive flag, and tags. This step also records the extracted verdict (ACCEPT or REJECT) — for System A configurations the verdict comes from the review's native `Decision` field; for the other four configurations the pipeline infers it from review text using a default-REJECT rule (see `data/audit/README.md` for the sensitivity audit).

Skill: `.claude/skills/skill-2-agentic-concern-extraction/SKILL.md`. Schema: `schemas/agentic_concern_sheet.schema.yaml`.

### Step 3 — Build concern match graph

Input: official + agentic concern sheets for one paper × system configuration.
Output: `data/match_graphs/public_slice/<system_dir>/<paper_slug>.yaml` — a bipartite graph of matches with explicit labels for match type, judgment alignment, and severity alignment.

This is the core step. It distinguishes "did the system see the concern?" (match type), "did it reach the same conclusion?" (judgment alignment), and "did it weight it correctly?" (severity alignment). Unmatched official concerns are flagged as detection gaps; unmatched agentic concerns become phantoms.

Skill: `.claude/skills/skill-3-concern-match-graph/SKILL.md`. Schema: `schemas/match_graph.schema.yaml`.

### Step 4 — Verify edges

Input: match graph + source documents (official review, paper, agentic review).
Output: `data/overrides/public_slice/semantic_overrides.yaml`.

An independent LLM pass re-judges each strict match edge and each unmatched concern to catch optimistic or missed matches. The verifier reads structured audit worksheets that present evidence neutrally — concern texts copied verbatim, match labels, severities, Jaccard scores side by side — so the verifier does not anchor on the first-pass framing. It must not see verdicts, error types, or ground truth.

Skill: `.claude/skills/skill-5b-semantic-edge-verification/SKILL.md`. Schema: `schemas/semantic_override.schema.yaml`.

### Step 5 — Aggregate metrics

Input: all verified match graphs for the benchmark (for the 48-paper set: 864 graphs across 6 configs × 48 papers × 3 runs; for the 9-paper Named Papers public slice: 54 graphs).
Output: `data/reports/public_slice/aggregate_report.md` and `data/metrics/public_slice/alignment_metrics.txt` — per-system L0–L4 metrics, bootstrap confidence intervals, error-type stratification, concern-type breakdowns, and phantom analysis.

Skill: `.claude/skills/skill-4-alignment-aggregate/SKILL.md`.

## Running the pipeline

The pipeline is driven interactively from Claude Code. Clone the repo, run `claude`, and paste the one-prompt skill sequence from the [Quick Start](../README.md#quick-start) in the project README (or the Try-it tab of the demo). The skills enforce step ordering and read the required schemas before producing each artifact.

## Two scopes

The pipeline runs against two datasets in this repository:

- The **48-paper safety/alignment benchmark** (`calibration_set: 6` in `data/ground_truth.yaml`) is the dataset behind the paper's headline numbers. It includes 6 baseline configurations × 48 papers × 3 runs = 864 match graphs.
- The **9-paper Named Papers public slice** (`calibration_set: public_slice`) is a curated subset used for per-paper case studies. It includes 6 baseline configurations × 9 papers × 1 run = 54 match graphs, plus full end-to-end artifacts (raw review text, OpenReview threads, extracted concern sheets) for public inspection.

Both datasets use the same pipeline, schemas. Case studies live under `docs/case_studies/public_slice/`; the aggregate report covers the 9-paper slice.

## Further reading

- Framework and metric definitions: `concern_alignment_evaluation.md`
- Case studies for the 9-paper slice: `docs/case_studies/public_slice/`
- Verdict inference audit (methodology and reconciled CSVs for both datasets): `data/audit/README.md`
- Schemas for every artifact type: `schemas/`
