# Baseline Profile: System L · GPT-4o

**Method family**: Liang  
**Released configuration**: GPT-4o  
**Public framing**: **selective and comparatively well calibrated**

> **Verdict-inference scope.** Verdict accuracy in this profile is inferred from review tone or structure by our extraction pipeline. Both System A configurations (Opus and GPT-4o) emit a native Decision field; this profile is not one of them. Both the 9-paper Named Papers table and the 48-paper benchmark table on this page are **single run (run 1)**; the homepage displays 3-run means and will not numerically match. The same caveat applies to per-paper verdict tables and any verdict prose later on this page. The paper appendix's sensitivity audit (covering a separate 48-paper safety/alignment benchmark) shows verdict-level numbers vary with inference method, while concern-level metrics — recall, FDR, decisive precision, phantom rates — do not. The audit has since been extended to the 9-paper public slice. System L · GPT-4o's final (audited) verdict differs from its pipeline verdict on 2 of 9 papers: one pipeline REJECT becomes ACCEPT on `rl_backtracking_feedback` under tone consensus, and one pipeline ACCEPT becomes AMBIGUOUS on `beyond_problem_solving` under rater disagreement. This matches its high tone-method volatility on the 48-paper benchmark. On the 9-paper slice it still shows audited flips (2/9), but the slice is too small to support a strongest-configuration ranking — System M · GPT-4o has more tone disagreements on the public slice in absolute terms (driven by structural artifacts), and L · GPT-4o is best described as one of the more tone-sensitive inferred configurations.

### Named Papers slice (9 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 77.8% |
| TP/TN/FP/FN | 6/1/1/1 |
| Recall (strict) | 22.4% |
| Recall (loose) | 27.0% |
| Precision | 69.4% |
| Phantom rate | 30.6% |
| Decisive recall | 29.2% |

### Full benchmark context (48 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 54.2% |
| Accepted-paper accuracy | 62.5% |
| Rejected-paper accuracy | 45.8% |
| Average strict recall | 24.2% |
| Average phantom rate | 39.4% |

## Behavioral profile

System L · GPT-4o posts the highest raw verdict accuracy in the Named Papers slice. It accepts six of the seven accepted papers and correctly rejects one of the two rejected papers. The concern-level view shows why: the configuration is selective. It raises fewer concerns than the more expansive configurations and carries the lowest phantom rate in the slice.

The tradeoff is coverage. The configuration does not recover as many official concerns as more exhaustive configurations, so its verdict performance is best described as **selective calibration** rather than comprehensive understanding.

## Representative papers

### 1. `artificial_hivemind`

A selective configuration accepting a celebrated paper for reasonable reasons. The configuration recovers part of the official concerns, recognizes the empirical contribution, and lands on the correct side of the decision.

### 2. `rl_backtracking_feedback`

The lone false negative in the Named Papers slice. The configuration misses too much of the accepted-paper rationale and ends up rejecting a paper that the venue accepted.

### 3. `beyond_problem_solving`

The configuration's lone false positive in the slice. A strong top-line accuracy number does not translate into universal reliability.

## Named Papers verdict table

| Paper | Decision | Verdict | Error | Strict recall | Loose recall | AI concerns |
|---|---|---|---|---|---|---|
| adversarial_dejavu | ACCEPTED | ACCEPT | TP | 18.2% | 18.2% | 4 |
| artificial_hivemind | ACCEPTED | ACCEPT | TP | 26.3% | 36.8% | 7 |
| beyond_problem_solving | REJECTED | ACCEPT | FP | 22.2% | 33.3% | 4 |
| cmdp_meta_safe_rl | ACCEPTED | ACCEPT | TP | 36.8% | 36.8% | 7 |
| collabllm | ACCEPTED | ACCEPT | TP | 27.3% | 27.3% | 4 |
| from_assistant_pentest | REJECTED | REJECT | TN | 30.0% | 40.0% | 8 |
| from_capabilities_pentest | ACCEPTED | ACCEPT | TP | 10.0% | 20.0% | 6 |
| rl_backtracking_feedback | ACCEPTED | REJECT | FN | 7.7% | 7.7% | 4 |
| rl_reasoning_limits | ACCEPTED | ACCEPT | TP | 23.1% | 23.1% | 5 |
