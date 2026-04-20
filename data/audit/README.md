# Verdict Inference Audit — Vendored Data (9-paper public slice)

This directory ships the reconciled audit artifact for the **9-paper Named Papers public slice** — the dataset behind the case studies under `docs/case_studies/public_slice/`. It uses a three-method, two-rater design with human adjudication on disagreements.

- `verdict_inference_named_9.csv` is the **9-paper public slice audit**. It was run to validate the per-paper verdict headlines in the case studies under `docs/case_studies/public_slice/`. The working directory and rater-prompt package under `named_9/` document the full reproduction recipe.

The analogous audit over the **48-paper safety/alignment benchmark** (288 reviews) is reported in the paper appendix. Its per-review CSV is intentionally not vendored in the public release; contact the author if you need it for replication.

## Contents

| File | Description |
|---|---|
| `verdict_inference_named_9.csv` | All 54 reviews (9 papers × 6 baseline configurations × run 1) on the 9-paper Named Papers public slice, with one row per review, showing the official venue decision, our extraction pipeline's verdict, two independent raters' tone- and gate-based verdicts, the human-adjudicated verdict where applicable, and the final resolved verdict. Two raters (Claude Opus and ChatGPT 5.4 Pro Extended Thinking), three methods (pipeline / tone / gate), and human adjudication on 20 cases (14 tier-1 rater disagreements plus 6 tier-2 method disagreements). 34 of the 54 reviews reached full four-cell agreement and auto-resolved. |
| `named_9/` | Working directory for the 9-paper audit: the Claude rater's raw output (`verdict_inference_named_9_cc.csv`), the external rater's batch outputs (`batch_*_results.csv`, `all_batches_results.csv`), a batch summary note, and the adjudication queue (`adjudication_queue.csv`). These are kept for transparency; the reconciled CSV above is the citation-grade artifact. |

## Column schema

| Column | Values | Meaning |
|---|---|---|
| `paper_slug` | string | Stable identifier for the paper (matches `data/papers/` and `data/reviews/` slugs). |
| `system` | `A`, `L`, `M`, `O` | Baseline method family (System A · AI Scientist; System L · Liang; System M · MARG; System O · OAR). |
| `model` | `GPT4o`, `Opus` | Model used in this configuration. |
| `official_decision` | `ACCEPT`, `REJECT` | Venue decision from OpenReview. Ground truth. |
| `pipeline_verdict` | `ACCEPT`, `REJECT` | Verdict produced by our extraction pipeline (Claude Sonnet, default-REJECT rule). Binary by construction. The number that appears in the website headline tables and case studies. |
| `cc_tone` | `ACCEPT`, `REJECT`, `AMBIGUOUS` | Rater 1 (Claude Code rater, Opus) — independent tone reading of the raw review text, no default-REJECT bias. |
| `ext_tone` | `ACCEPT`, `REJECT`, `AMBIGUOUS` | Rater 2 (ChatGPT 5.4 Pro Extended Thinking) — independent tone reading. |
| `cc_gate` | `ACCEPT`, `REJECT`, `AMBIGUOUS` | Rater 1 — gate-based verdict: classifies each major/fatal concern into gate categories (G0–G7), then applies deterministic rules (fatal → REJECT; 2+ fundamental hits → REJECT; 0 hits + accept signal → ACCEPT; else AMBIGUOUS). |
| `ext_gate` | `ACCEPT`, `REJECT`, `AMBIGUOUS` | Rater 2 — gate-based verdict. |
| `human_verdict` | `ACCEPT`, `REJECT`, `UNRELIABLE`, blank | Human adjudication. Populated only for cases entered into the audit queue (rater disagreements and tone/gate divergences); blank for cases where automated raters agreed. `UNRELIABLE` flags reviews that cannot be assigned a coherent verdict regardless of method (this is the System M coordination-artifact case). |
| `final_verdict` | `ACCEPT`, `REJECT`, `AMBIGUOUS`, `UNRELIABLE` | Resolved verdict combining all sources. Equal to `human_verdict` where present, else inherits the consensus of automated raters, else inherits `pipeline_verdict`. `AMBIGUOUS` appears when adjudication could not assign a coherent binary verdict (e.g. tier-2 method-divergence cases that remained split). |
| `audited` | `YES`, `NO` | Whether the case was hand-audited. In the 9-paper CSV (54 rows), 20 of the 54 cases entered the adjudication queue (14 tier-1 rater disagreements plus 6 tier-2 method divergences); the remaining 34 reached full four-cell rater agreement and auto-resolved. |

## Working directory for the 9-paper audit

The `named_9/` subdirectory contains the raw outputs and intermediate artifacts from the 9-paper audit:

- `verdict_inference_named_9_cc.csv` — Rater 1 (Claude Opus) raw output with per-concern gate classifications and reasoning.
- `all_batches_results.csv`, `batch_01_results.csv`, `batch_02_results.csv`, `batch_03_results.csv` — Rater 2 (ChatGPT 5.4 Pro Extended Thinking) outputs; the combined file and per-batch breakdowns (9 papers were sent to the external rater in three batches of three).
- `batch_summaries.md` — per-batch narrative notes from Rater 2.
- `adjudication_queue.csv` — the 20-case queue used to resolve rater disagreements (14 tier-1 + 6 tier-2); the reconciled outcomes are folded into `verdict_inference_named_9.csv` at the parent level.
- `ext_rater_prompts/` — the external-rater prompt package (instructions, gate definitions, output schema, worked examples) shipped to Rater 2.

## Relationship to the 48-paper benchmark audit

The paper's sensitivity audit covers all 288 reviews of the 48-paper safety/alignment benchmark (48 papers × 6 baseline configurations × run 1) with the same three-method, two-rater design and 54 hand-audited cases. That audit — including headline numbers, per-configuration flip rates, and the L · Opus ↔ L · GPT-4o 46–96 pp swing — is reported in the paper appendix and is the authoritative reference. The 9-paper audit here is a website-side follow-up on the public slice and reuses the same methodology.

Per-review artifacts for the 48-paper benchmark audit (the 288-row reconciled CSV, both raters' raw output CSVs, the full human audit document, and per-tier disagreement queues) are intentionally not vendored in this public release. They live in the upstream research repository. Contact the author or open an issue if you need them for replication.

## How to read the audit

A few patterns in the data are load-bearing for the paper's claims:

1. **System M reviews are flagged `UNRELIABLE` in `human_verdict` and `final_verdict`** because the multi-agent coordination artifacts (inter-agent messages, repeated draft fragments) make any verdict reading more about the artifact than about the system's intended recommendation. This is independent of the inference method.

2. **`pipeline_verdict` is binary** (ACCEPT/REJECT only), while `cc_tone`, `ext_tone`, `cc_gate`, `ext_gate` admit AMBIGUOUS. Counting AMBIGUOUS as REJECT (the pipeline default) versus splitting it differently is the lever that produces the 46–96 percentage-point swing in System L's accepted-paper accuracy reported in the paper appendix. The 9-paper slice is a smaller sample and the swing is noisier, but it follows the same pattern.

3. **The pipeline is kept as the primary reporting method** across the website and README. The audit is presented as a sensitivity analysis, not as a correction. Concern-level metrics (recall, FDR, decisive precision, phantom rates) are stable across all inference methods; verdict-level metrics are not. This stability gap is itself the diagnostic finding.

## Citation and provenance

If you use this CSV, cite the paper's verdict inference audit appendix. The 9-paper audit here was executed in April 2026 against run 1 of the Named Papers public slice using the same methodology as the paper's 48-paper audit.
