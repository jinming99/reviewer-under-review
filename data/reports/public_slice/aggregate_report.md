# Aggregate Concern Alignment Report — public_slice

**Scope**: 9-paper Named Papers slice  
**Decision balance**: 7 accepted, 2 rejected  
**Official concerns**: 150 total (102 resolved in rebuttal, 48 unresolved, 7 decisive blockers)  
**Released match graphs**: 54 (9 papers across 6 baseline configurations)  
**Methods included**: System A · GPT-4o, System A · Opus, System L · GPT-4o, System L · Opus, System M · GPT-4o, System O · Opus

> **Verdict-inference scope.** Verdict accuracy in this report is inferred from each system's review tone or structure by our extraction pipeline. Native verdicts are produced by both System A configurations (Opus and GPT-4o), which emit an explicit Decision field; for the other four configurations the verdict is inferred. The 9-paper table in §2 and the 48-paper table in §3 are both **single run (run 1)** and will not numerically match the homepage, which displays 3-run means. The paper appendix's sensitivity audit (covering a separate 48-paper safety/alignment benchmark) shows verdict-level numbers vary with inference method, while concern-level metrics — recall, FDR, decisive precision, phantom rates — do not. The audit has since been extended to the 9-paper public slice this report covers. Per-configuration flip rate: System A · GPT-4o 0/9, System A · Opus 0/9, System L · GPT-4o 2/9, System L · Opus 0/9, System M · GPT-4o 7/9 (all to UNRELIABLE), System O · Opus 1/9. The audited CSV lives at `data/audit/verdict_inference_named_9.csv`; the demo's Verdict Sensitivity panel (Named Papers segment) has the interactive breakdown. System M reviews additionally contain multi-agent coordination artifacts that make verdict inference unreliable for that configuration regardless of method.

---

## 1. What this report is

This report is the aggregate view for the **Named Papers** slice: nine papers with known venue outcomes and end-to-end public artifacts. It is diagnostic rather than leaderboard-oriented. With only nine papers, the numbers are best read as a profile of system behavior under the released evaluation conditions.

## 2. Subset-level system snapshot (9-paper Named Papers slice)

| Method | Accuracy | TP/TN/FP/FN | Recall (strict) | Recall (loose) | Precision | Phantom rate | Decisive recall |
|---|---|---|---|---|---|---|---|
| System L · GPT-4o | 77.8% | 6/1/1/1 | 22.4% | 27.0% | 69.4% | 30.6% | 29.2% |
| System M · GPT-4o | 44.4% | 3/1/1/4 | 33.0% | 43.9% | 57.6% | 42.4% | 29.2% |
| System O · Opus | 44.4% | 2/2/0/5 | 13.2% | 27.7% | 28.6% | 71.4% | 0.0% |
| System A · Opus | 33.3% | 1/2/0/6 | 32.7% | 38.0% | 48.4% | 51.6% | 62.5% |
| System L · Opus | 22.2% | 0/2/0/7 | 30.3% | 38.7% | 63.1% | 36.9% | 50.0% |
| System A · GPT-4o | 22.2% | 0/2/0/7 | 20.2% | 26.1% | 60.4% | 39.6% | 25.0% |

### Reading notes

- Accuracy is raw verdict agreement on the 9-paper Named Papers slice.
- Precision is the fraction of AI concerns that participate in at least one match edge.
- Phantom rate is the fraction of AI concerns with no match edge.
- Decisive recall is defined only on the two rejected papers, where official decisive blockers exist, and is averaged across those two papers.

## 3. Full-benchmark context (48-paper calibration set)

The repo and demo also report a **48-paper calibration set**. Those totals are benchmark-wide metrics, not properties of the 9-paper Named Papers slice.

| Method | Papers | Accuracy | Accepted accuracy | Rejected accuracy | Avg strict recall | Avg phantom rate |
|---|---|---|---|---|---|---|
| System A · GPT-4o | 48 | 50.0% | 0.0% | 100.0% | 19.9% | 46.0% |
| System A · Opus | 48 | 45.8% | 4.2% | 87.5% | 43.6% | 48.9% |
| System L · GPT-4o | 48 | 54.2% | 62.5% | 45.8% | 24.2% | 39.4% |
| System L · Opus | 48 | 50.0% | 0.0% | 100.0% | 39.4% | 41.7% |
| System M · GPT-4o † | 48 | 56.2% | 58.3% | 54.2% | 31.4% | 60.1% |
| System O · Opus | 48 | 54.2% | 29.2% | 79.2% | 13.9% | 79.8% |

†System M: all 48 reviews contain multi-agent coordination artifacts; verdict inference is unreliable for this configuration regardless of method. The accepted-paper accuracy reflects our pipeline's interpretation; under alternative inference methods this figure ranges widely.

The 48-paper calibration set carries benchmark-wide totals of **864 match graphs, 670 official concerns, and 79 decisive blockers**. The 9-paper Named Papers slice carries **54 released match graphs and 150 official concerns**, as summarized at the top of this file.

## 4. Paper-set summary (9-paper Named Papers slice)

| Paper | Venue | Decision | Official concerns | Scores (pre) | Scores (post) |
|---|---|---|---|---|---|
| adversarial_dejavu | ICLR 2026 | ACCEPTED | 22 | [6, 2, 8, 6] | [6, 6, 8, 6] |
| artificial_hivemind | NeurIPS 2025 | ACCEPTED | 19 | [6, 2, 4, 5] | [6, 4, 4, 5] |
| beyond_problem_solving | ACL ARR 2025 July | REJECTED | 9 | [2, 2, 3.5] | [2, 2, 3.5] |
| cmdp_meta_safe_rl | ICLR 2023 | ACCEPTED | 19 | [8, 6, 3] | [8, 6, 3] |
| collabllm | ICML 2025 | ACCEPTED | 22 | [4, 4, 4, 4, 4] | [4, 4, 4, 4, 4] |
| from_assistant_pentest | ACL ARR Feb 2025 | REJECTED | 10 | [2.5, 2.5, 1.5] | — (no post-rebuttal) |
| from_capabilities_pentest | ACL ARR May 2025 | ACCEPTED | 10 | [3.5, 3.0, 3.5] | [3.5, 3.5, 3.5] |
| rl_backtracking_feedback | NeurIPS 2025 | ACCEPTED | 13 | [5, 4, 4, 5] | [5, 4, 4, 5] |
| rl_reasoning_limits | NeurIPS 2025 | ACCEPTED | 26 | [5, 6, 5, 5] | [6, 6, 6, 6] |

## 5. Per-paper verdict consensus (9-paper Named Papers slice)

| Paper | Decision | Official concerns | Correct methods (of 6) | TP/TN/FP/FN |
|---|---|---|---|---|
| rl_backtracking_feedback | accepted | 13 | 0 | 0/0/0/6 |
| cmdp_meta_safe_rl | accepted | 19 | 1 | 1/0/0/5 |
| rl_reasoning_limits | accepted | 26 | 1 | 1/0/0/5 |
| artificial_hivemind | accepted | 19 | 2 | 2/0/0/4 |
| from_capabilities_pentest | accepted | 10 | 2 | 2/0/0/4 |
| adversarial_dejavu | accepted | 22 | 3 | 3/0/0/3 |
| collabllm | accepted | 22 | 3 | 3/0/0/3 |
| beyond_problem_solving | rejected | 9 | 5 | 0/5/1/0 |
| from_assistant_pentest | rejected | 10 | 5 | 0/5/1/0 |

### Interpretation

- The hardest paper in this slice is **`rl_backtracking_feedback`**: under the pipeline headline extraction all six baselines reject an accepted paper; under the follow-up audit five of six still reject and one (System L · GPT-4o) flips to ACCEPT.
- The two rejected papers are comparatively easy at the verdict level: five of six systems are correct on each, with **System M · GPT-4o** the lone false positive on `from_assistant_pentest` and **System L · GPT-4o** the lone false positive on `beyond_problem_solving`.
- With only nine papers, the slice is most useful for calibration stories on accepted papers and is not intended to support broad ranking claims.

## 6. Concern coverage by issue type (9-paper Named Papers slice)

| Issue type | Official total | A/GPT-4o strict | A/Opus strict | L/GPT-4o strict | L/Opus strict | M/GPT-4o strict | O/Opus strict |
|---|---|---|---|---|---|---|---|
| empirical | 75 | 10.7% | 37.3% | 24.0% | 32.0% | 32.0% | 13.3% |
| conceptual | 46 | 32.6% | 32.6% | 28.3% | 30.4% | 28.3% | 10.9% |
| framing | 29 | 17.2% | 10.3% | 13.8% | 6.9% | 17.2% | 0.0% |

### What stands out

- Empirical concerns dominate this slice (75 of 150 official concerns).
- Framing concerns remain the sparsest category for most systems.
- `System O · Opus` sits at 0.0% on framing concerns in this slice.

## 7. Resolved, unresolved, and decisive concerns (9-paper Named Papers slice)

| Method | Resolved strict recall | Unresolved strict recall | Decisive strict recall |
|---|---|---|---|
| System A · GPT-4o | 16.7% | 22.9% | 28.6% |
| System A · Opus | 29.4% | 33.3% | 57.1% |
| System L · GPT-4o | 22.5% | 25.0% | 28.6% |
| System L · Opus | 22.5% | 35.4% | 42.9% |
| System M · GPT-4o | 26.5% | 31.2% | 28.6% |
| System O · Opus | 8.8% | 12.5% | 0.0% |

Decisive strict recall here is pooled across the 7 decisive blockers in the 9-paper Named Papers slice. The decisive recall column in section 2 is a per-paper average over the two rejected papers, which explains the different numbers in the two views.

### Interpretation

- `System A · Opus` has the highest decisive recall on this slice, which does not translate into high verdict accuracy on accepted papers.
- `System L · GPT-4o` has the strongest verdict accuracy on this slice while posting relatively modest decisive recall. The method behaves selectively.
- `System O · Opus` produces detailed technical auditing whose content aligns weakly with the concerns that drove the official decisions.

## 8. Match-type composition (9-paper Named Papers slice)

| Method | Exact edges | Partial edges | Related edges | Matched AI concerns | Total AI concerns |
|---|---|---|---|---|---|
| System A · GPT-4o | 6 | 24 | 9 | 32 | 53 |
| System A · Opus | 18 | 28 | 8 | 46 | 95 |
| System L · GPT-4o | 15 | 21 | 6 | 34 | 49 |
| System L · Opus | 11 | 29 | 13 | 41 | 65 |
| System M · GPT-4o | 8 | 37 | 17 | 53 | 92 |
| System O · Opus | 4 | 14 | 22 | 38 | 133 |

## 9. Frequently missed official tags (9-paper Named Papers slice)

| Tag | Official total | Average strict recall (6 methods) | A/GPT-4o | A/Opus | L/GPT-4o | L/Opus | M/GPT-4o | O/Opus |
|---|---|---|---|---|---|---|---|---|
| formatting | 3 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| visualization | 3 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| related_work | 8 | 4.2% | 0.0% | 0.0% | 12.5% | 0.0% | 12.5% | 0.0% |
| positioning | 4 | 8.3% | 0.0% | 0.0% | 25.0% | 0.0% | 25.0% | 0.0% |
| robustness | 4 | 12.5% | 0.0% | 25.0% | 0.0% | 0.0% | 25.0% | 25.0% |
| presentation | 12 | 15.3% | 16.7% | 16.7% | 16.7% | 8.3% | 25.0% | 8.3% |
| analysis_depth | 3 | 16.7% | 0.0% | 33.3% | 33.3% | 0.0% | 33.3% | 0.0% |
| baseline_comparison | 3 | 16.7% | 0.0% | 66.7% | 0.0% | 33.3% | 0.0% | 0.0% |
| generalizability | 9 | 22.2% | 33.3% | 22.2% | 55.6% | 11.1% | 11.1% | 0.0% |
| ablation | 6 | 22.2% | 16.7% | 66.7% | 0.0% | 16.7% | 33.3% | 0.0% |
| paper_organization | 3 | 22.2% | 33.3% | 33.3% | 0.0% | 33.3% | 33.3% | 0.0% |
| novelty_delta | 4 | 25.0% | 100.0% | 25.0% | 0.0% | 25.0% | 0.0% | 0.0% |

These tags are candidates for future rubric work and for a stronger workflow-level alignment framing. They point to recurring blind spots in how automated reviewers prioritize literature positioning, framing, and presentation-level scientific communication.

## 10. Overall pattern

On the 9-paper Named Papers slice, the baseline systems show a familiar pattern: verdict agreement alone is not enough to explain review quality. `System L · GPT-4o` is the strongest on raw verdict accuracy in this slice, while `System A · Opus` is stronger at recovering decisive blockers. `System O · Opus` produces detailed technical auditing whose content aligns weakly with the concerns that drove the official decisions. The most informative failures occur on accepted papers, where several systems surface real concerns but miscalibrate how much those concerns should count.
