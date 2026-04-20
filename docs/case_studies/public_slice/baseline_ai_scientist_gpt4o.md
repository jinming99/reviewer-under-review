# Baseline Profile: System A · GPT-4o

**Method family**: AI Scientist  
**Released configuration**: GPT-4o  
**Public framing**: **brief and selective, with a reject-skewed verdict pattern**

> **Verdict-inference scope.** Both System A configurations (Opus and GPT-4o) emit an explicit Decision field in their review output — this profile is one of the two native-verdict configurations. The other four baseline profiles use verdicts inferred from review text by our extraction pipeline. Both the 9-paper Named Papers table and the 48-paper benchmark table on this page are **single run (run 1)**; the homepage displays 3-run means and will not numerically match. The paper appendix's sensitivity audit (covering a separate 48-paper safety/alignment benchmark) shows verdict-level numbers vary with inference method for the inferred configurations, while concern-level metrics — recall, FDR, decisive precision, phantom rates — do not. The audit has since been extended to the 9-paper public slice. System A · GPT-4o's final (audited) verdict equals its pipeline verdict on all 9 papers — zero flips. Three configurations share this 0/9 pattern on the public slice (both System A configurations plus System L · Opus); the other three each flip on at least one paper.

### Named Papers slice (9 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 22.2% |
| TP/TN/FP/FN | 0/2/0/7 |
| Recall (strict) | 20.2% |
| Recall (loose) | 26.1% |
| Precision | 60.4% |
| Phantom rate | 39.6% |
| Decisive recall | 28.6% |

### Full benchmark context (48 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 50.0% |
| Accepted-paper accuracy | 0.0% |
| Rejected-paper accuracy | 100.0% |
| Average strict recall | 19.9% |
| Average phantom rate | 46.0% |


## Behavioral profile

System A · GPT-4o is the leaner, more selective sibling of the Opus configuration. In the Named Papers slice it produces fewer concerns overall and keeps a lower phantom rate than the more expansive systems. The tradeoff is coverage: it recovers a smaller share of official concerns on accepted papers, and the verdict pattern is strongly reject-skewed. The result is a review profile that is concise and often sensible locally, yet reject-skewed at the verdict level.

The concern-alignment observation here is not simply that the review is shorter. It is that lower-volume reviewing without corresponding selectivity gains can still land on the wrong verdict. In the Named Papers slice, the configuration agrees with the human decision only on the two rejected papers.

## Where the profile is most informative

### 1. `from_assistant_pentest` (correct rejection)

This is the cleanest case where the configuration's skeptical posture lines up with the human decision. The case is useful because it shows that the method can still be directionally correct when the blockers are obvious.

### 2. `cmdp_meta_safe_rl` (incorrect rejection despite relatively strong recall)

The pattern here shows why verdict agreement alone is incomplete as a signal. The method recovers a meaningful fraction of the official concerns and still rejects a paper that was accepted. The pattern points to weighting, not total blindness.

### 3. `collabllm` and `artificial_hivemind` (thin coverage on accepted papers)

These papers show the coverage cost of the selective profile. The method raises some legitimate issues, but it does not recover enough of the accepted-paper rationale to calibrate the verdict.

## Named Papers verdict table

| Paper | Decision | Verdict | Error | Strict recall | Loose recall | AI concerns |
|---|---|---|---|---|---|---|
| adversarial_dejavu | ACCEPTED | REJECT (3) | FN | 18.2% | 18.2% | 8 |
| artificial_hivemind | ACCEPTED | REJECT (5) | FN | 10.5% | 15.8% | 4 |
| beyond_problem_solving | REJECTED | REJECT | TN | 22.2% | 33.3% | 6 |
| cmdp_meta_safe_rl | ACCEPTED | REJECT (3) | FN | 42.1% | 47.4% | 7 |
| collabllm | ACCEPTED | REJECT (3) | FN | 9.1% | 18.2% | 5 |
| from_assistant_pentest | REJECTED | REJECT (3) | TN | 30.0% | 30.0% | 5 |
| from_capabilities_pentest | ACCEPTED | REJECT (3) | FN | 30.0% | 30.0% | 7 |
| rl_backtracking_feedback | ACCEPTED | REJECT (4) | FN | 7.7% | 30.8% | 7 |
| rl_reasoning_limits | ACCEPTED | REJECT (3) | FN | 11.5% | 11.5% | 4 |
