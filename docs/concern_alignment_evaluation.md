# Concern-Alignment Evaluation Framework

## Motivation

Binary accept/reject accuracy has hit a diagnostic ceiling. Across the 48-paper safety/alignment benchmark that backs this project's headline numbers, the six evaluated baseline configurations cluster in a 50.7–60.4% accuracy band (3-run means; the 48-paper single-run pipeline range is 45.8–56.2%) — close enough to a coin flip on a balanced set that the score itself cannot distinguish a reject-heavy reviewer from a low-recall reviewer from a well-calibrated one. More importantly, binary accuracy cannot diagnose **why** a system fails. Two papers with the same wrong verdict can fail for entirely different reasons:

- **Wrong verdict, right concerns**: the system flagged the same issues as the official reviewers but miscalibrated severity (for example, flagged the AC's decisive concern but called it "major-addressable" when the AC called it "fatal").
- **Wrong verdict, wrong concerns**: the system focused on entirely different issues than the official reviewers (for example, demanded more benchmarks when the real concern was conceptual novelty).

Concern-alignment evaluation measures **what** the system flags and **how severely**, not just whether the final binary matches. This produces actionable diagnostics — which concerns the system systematically misses, which ones it mis-weights, and which ones it fabricates without grounding in the official record.

## The five-level evaluation ladder

Each level reveals a failure mode invisible to the level below.

| Level | Question | What it catches |
|-------|----------|-----------------|
| **L0** | Does the system get accept/reject right? | Nothing useful on its own; a reject-everything system and a random one are indistinguishable on a balanced set. |
| **L1** | Does the system find the real issues? | Phantom concerns (no grounding in the official record) and detection gaps (official concerns the system missed entirely). |
| **L2** | Is accuracy balanced? | "50% accurate" can mean 0% on accepted papers (reject-heavy behavior) and 100% on rejected papers. |
| **L3** | When the system says "fatal," is it right? | False decisive rate: how often the system cries wolf on papers the venue accepted. |
| **L4** | Does the system focus on what the area chair cared about? | Inverted attention: some systems catch resolved concerns but miss the actual blockers. |

L0 is the binary accuracy the rest of the literature reports. L1–L4 are the diagnostics this project contributes. The paper quantifies each level on the 48-paper benchmark; the case studies under `docs/case_studies/public_slice/` walk the ladder on one paper at a time for the 9-paper Named Papers public slice.

---

## The match graph

The core artifact is a **bipartite match graph** between the official reviewer concerns for a paper and the concerns extracted from an AI reviewer's output for the same paper. Every edge carries three labels:

- **Match type**: `exact`, `partial`, or `related`. Did the system see the concern at all? (Concerns with no edge at all are unmatched — misses on the official side, phantoms on the agentic side.)
- **Judgment alignment**: `aligned`, `inverted`, or `mixed`. When both sides address the same fact, did they reach the same conclusion?
- **Severity alignment**: `match`, `under`, or `over`. Did the system weight the concern at the right level?

Official concerns with no `exact` or `partial` edge are **detection gaps**: issues the AI reviewer missed. Agentic concerns with no `exact` or `partial` edge are **phantoms**: issues the AI reviewer raised that have no grounding in the official record (`related` edges are excluded from strict metrics for this reason). Phantoms are not necessarily errors — some are legitimate additions the human reviewers missed. But most are misses of a different kind: the system generated concern-shaped text without evidence.

The match graph is what distinguishes "did the system see the concern?" (match type) from "did the system understand the concern?" (judgment alignment) from "did the system weight the concern correctly?" (severity alignment). A single binary accept/reject collapses all three into one bit of information; the match graph preserves them as independent diagnostics.

### Severity alignment policy

When AI and official severities agree exactly, the label is `match`. When they differ, the label depends on how the boundary is crossed:

- **One-level gaps among non-fatal concerns** (e.g., `major` ↔ `moderate`, `moderate` ↔ `minor`) are labeled `match`. These are within annotator noise.
- **Crossing the fatal boundary** (`fatal` ↔ anything else) is labeled `under` or `over` directionally. Fatal is a decision-changing severity level, not an intensity knob.
- **Crossing the decisive-blocker boundary** (one side is `decisive_blocker` in the AC's treatment, the other side is non-decisive) is labeled `under` or `over`. This captures the clearest calibration errors, where the system disagreed with the venue on what was blocking.

This policy is applied mechanically to every edge in every match graph. Severity calibration is not surfaced as a single public metric; it shows up through the ladder's decision-aware metrics — L2 verdict-stratified accuracy, L3 false decisive rate on accepted papers and decisive precision on rejected papers, and the under/over distributions reported in the per-system profiles.

---

## The concern-extraction pipeline

A five-step pipeline builds every match graph. Detailed step-by-step paths, schemas, and skills are in [`pipeline_meta_eval.md`](pipeline_meta_eval.md); the short version:

1. **Extract official concerns** from the OpenReview thread (reviews, rebuttal, meta-review) for each paper. One structured YAML per paper, shared across all six system configurations.
2. **Extract agentic concerns** from each AI reviewer's output on each paper. One YAML per paper × configuration.
3. **Build the match graph** between the two concern sheets for each paper × configuration.
4. **Verify edges** with an independent LLM pass that re-judges match type, judgment alignment, and severity alignment against the source documents; flag optimistic or missed matches.
5. **Aggregate metrics** across all match graphs to produce L0–L4 metrics per system configuration, with bootstrap confidence intervals.

All artifacts are schema-validated (`schemas/`) and lint-checked (`rur lint`). The `rur metrics` CLI produces the aggregate report from the verified match graphs.

---

## Tag vocabulary

Concerns are tagged at extraction time with issue-type and topic tags. The tag vocabulary is flexible and emergent — new tags can be added when a recurring issue type lacks coverage — but the following seed tags cover the common patterns in the 48-paper benchmark.

**Issue-type tags** (what kind of reviewer concern is this):

- `empirical` — evaluation scope, baselines, reproducibility, statistical significance, benchmark choice.
- `conceptual` — theoretical soundness, claim-evidence mismatch, construct validity, overgeneralization.
- `framing` — scope of the claim, positioning against prior work, writing clarity affecting interpretation of results.
- `presentation` — figures, tables, notation, typography, exposition (without affecting the result's validity).
- `ethics` — responsible-use considerations, dual-use risk, data provenance, consent.

**Topic tags** (what substantive area is the concern about) — these are paper-specific; examples from the 48-paper set include `attack_defensibility`, `construct_validity`, `practical_relevance`, `benchmark_longevity`, `novelty_delta`, `reproducibility`, `adversarial_robustness`, `metric_validity`.

Tagging rules:

- Tag both the official concern (at extraction time) and any matching agentic concern (mirroring the official tag when the match is exact or partial).
- A concern can carry multiple tags when the issue genuinely spans categories (e.g., an evaluation design flaw that also invalidates a conceptual claim).
- Keep tags atomic — one tag should describe one facet of the concern, not a conjunction.

The aggregate metrics stratify by tag to produce diagnostic statements like "this system misses 60% of `construct_validity` concerns but only 15% of `reproducibility` concerns."

---

## Benchmarks and case studies

This framework runs against two datasets in this repository:

- **48-paper safety/alignment benchmark** (`calibration_set: 6` in `data/ground_truth.yaml`). Balanced 24 accepted / 24 rejected. 6 baseline configurations × 48 papers × 3 runs = 864 match graphs. 670 official concerns extracted, with 79 decisive blockers. This is the dataset behind the paper's headline numbers.
- **9-paper Named Papers public slice** (`calibration_set: public_slice`). 7 accepted / 2 rejected, chosen to span celebrated contributions (a NeurIPS Outstanding Paper, a NeurIPS Oral, an ICML Oral, an ICLR Spotlight) and borderline or rejected papers. 6 baseline configurations × 9 papers × 1 run = 54 match graphs. Ships with full end-to-end artifacts — raw review text, OpenReview threads, extracted concern sheets — in the public release.

The case studies under `docs/case_studies/public_slice/` read the match graphs one paper at a time, comparing how each of the six configurations handled the same paper. This is where the framework's diagnostics become legible: the same binary score hides different pathologies, and the match graph is where those pathologies become visible.

---

## Two practical notes on reading the numbers

**Verdict inference.** Two of the six baseline configurations (both System A variants, Opus and GPT-4o) emit an explicit ACCEPT/REJECT field in their review output; their verdicts are native. The other four configurations do not emit a structured verdict; ours is inferred from review text by the extraction pipeline (a Claude Sonnet pass with a default-REJECT rule for ambiguous cases). A two-rater sensitivity audit on both datasets shows verdict-level numbers vary with the inference method, while concern-level diagnostics — recall, FDR, decisive precision, phantom rates, attention profiles — do not. The reconciled audit CSVs are at `data/audit/verdict_inference_final_288.csv` (48-paper) and `data/audit/verdict_inference_named_9.csv` (9-paper); the demo's Verdict Sensitivity panel has the interactive view.

**Run basis.** The paper's main-text numbers and the website homepage tables use 3-run means (each AI reviewer ran three independent times, per-paper metrics averaged). The case studies' per-paper verdict tables and the cross-surface 48-paper comparison table use single run (run 1) — re-running the audit on three runs was not cost-justified. When numbers do not match across surfaces, this is almost always why. Every public surface that displays verdict accuracy labels its run basis explicitly.

---

## Further reading

- Pipeline step-by-step with schemas and CLI: [`pipeline_meta_eval.md`](pipeline_meta_eval.md)
- Per-paper case studies walking the ladder: `docs/case_studies/public_slice/`
- Aggregate metrics for the 9-paper slice: `data/reports/public_slice/aggregate_report.md`
- Schemas for every artifact: `schemas/`
- Verdict inference audit methodology and reconciled data: `data/audit/README.md`
- Paper: `docs/concern-alignment-paper.pdf`
