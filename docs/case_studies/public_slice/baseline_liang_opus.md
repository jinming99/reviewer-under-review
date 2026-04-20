# Baseline Profile: System L · Opus

**Method family**: Liang  
**Released configuration**: Opus  
**Public framing**: **balanced prose, reject-leaning synthesis**

> **Verdict-inference scope.** Verdict accuracy in this profile is inferred from review tone or structure by our extraction pipeline. Both System A configurations (Opus and GPT-4o) emit a native Decision field; this profile is not one of them. Both the 9-paper Named Papers table and the 48-paper benchmark table on this page are **single run (run 1)**; the homepage displays 3-run means and will not numerically match. The same caveat applies to per-paper verdict tables and any verdict prose later on this page. The paper appendix's sensitivity audit (covering a separate 48-paper safety/alignment benchmark) shows verdict-level numbers vary with inference method, while concern-level metrics — recall, FDR, decisive precision, phantom rates — do not. The audit has since been extended to the 9-paper public slice. System L · Opus's final (audited) verdict equals its pipeline verdict on all 9 papers — zero flips. This is quieter than its 48-paper behavior (where it has 3–11 tone-method flips depending on rater); the public slice happens to be one where L · Opus reads consistently across methods.

### Public named-paper slice (9 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 22.2% |
| TP/TN/FP/FN | 0/2/0/7 |
| Recall (strict) | 30.3% |
| Recall (loose) | 38.7% |
| Precision | 63.1% |
| Phantom rate | 36.9% |
| Decisive recall | 50.0% |

### Full benchmark context (48 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 50.0% |
| Accepted-paper accuracy | 0.0% |
| Rejected-paper accuracy | 100.0% |
| Average strict recall | 39.4% |
| Average phantom rate | 41.7% |


## Behavioral profile

System L · Opus produces one of the most readable review styles in the Named Papers slice. It often sounds balanced because it names both strengths and weaknesses, and it maintains relatively good precision. The nine-paper slice nevertheless shows a clear reject-leaning outcome pattern: all seven accepted papers are rejected.

That asymmetry is the point of concern alignment. A review can read fair and thoughtful while still not converting its own observations into a well-calibrated decision. The method has relatively good precision and often surfaces real concerns, but it does not consistently translate those observations into a matching decision on accepted papers.

## Where the profile is most informative

### 1. `beyond_problem_solving` (correct rejection)

This is the configuration's strongest paper in the nine-paper slice. High strict recall and a correct direction show that the method can align well when the official record contains clear blocking concerns.

### 2. `artificial_hivemind` (wrong verdict despite comparatively strong recall)

This case is especially informative because the method recovers a relatively large share of the official concerns and still rejects an accepted, award-winning paper. The question is not one of missing every concern; it is how the concerns are synthesized.

### 3. `collabllm` and `from_capabilities_pentest` (balanced prose, reject result)

On these papers the reviews remain readable and analytically competent, while the decisions still skew reject. The profile stays legible without the prose itself sounding adversarial.

## Public nine-paper verdict table

| Paper | Decision | Verdict | Error | Strict recall | Loose recall | AI concerns |
|---|---|---|---|---|---|---|
| adversarial_dejavu | ACCEPTED | REJECT | FN | 9.1% | 13.6% | 4 |
| artificial_hivemind | ACCEPTED | REJECT | FN | 36.8% | 42.1% | 5 |
| beyond_problem_solving | REJECTED | REJECT | TN | 66.7% | 66.7% | 8 |
| cmdp_meta_safe_rl | ACCEPTED | REJECT | FN | 31.6% | 36.8% | 9 |
| collabllm | ACCEPTED | REJECT | FN | 18.2% | 27.3% | 4 |
| from_assistant_pentest | REJECTED | REJECT | TN | 30.0% | 60.0% | 8 |
| from_capabilities_pentest | ACCEPTED | REJECT | FN | 30.0% | 40.0% | 11 |
| rl_backtracking_feedback | ACCEPTED | REJECT | FN | 30.8% | 38.5% | 8 |
| rl_reasoning_limits | ACCEPTED | REJECT | FN | 19.2% | 23.1% | 8 |
