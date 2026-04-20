# Baseline Profile: System A · Opus

**Method family**: AI Scientist  
**Released configuration**: Opus  
**Framing**: **high detection, weak calibration**

> **Verdict-inference scope.** Both System A configurations (Opus and GPT-4o) emit an explicit Decision field in their review output — this profile is one of the two native-verdict configurations. The other four baseline profiles use verdicts inferred from review text by our extraction pipeline. Both the 9-paper Named Papers table and the 48-paper benchmark table on this page are **single run (run 1)**; the homepage displays 3-run means and will not numerically match. The same caveat applies to per-paper verdict tables and any verdict prose later on this page. The paper appendix's sensitivity audit (covering a separate 48-paper safety/alignment benchmark) shows verdict-level numbers vary with inference method for the inferred configurations, while concern-level metrics — recall, FDR, decisive precision, phantom rates — do not. The audit has since been extended to the 9-paper public slice. System A · Opus's final (audited) verdict equals its pipeline verdict on all 9 papers — zero flips. On the 48-paper benchmark, A · Opus shows 4/48 pipeline→final flips, so "method-stable" is accurate on the public slice specifically, not as a global claim.

### Named Papers slice (9 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 33.3% |
| TP/TN/FP/FN | 1/2/0/6 |
| Recall (strict) | 32.7% |
| Recall (loose) | 38.0% |
| Precision | 48.4% |
| Phantom rate | 51.6% |
| Decisive recall | 62.5% |

### Full benchmark context (48 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 45.8% |
| Accepted-paper accuracy | 4.2% |
| Rejected-paper accuracy | 87.5% |
| Average strict recall | 43.6% |
| Average phantom rate | 48.9% |


## Behavioral profile

System A · Opus is the most detection-oriented configuration in the Named Papers slice. It recovers a relatively large share of official concerns and has the highest decisive recall on the rejected papers, yet it still rejects most accepted papers. The resulting pattern is not "blindness" so much as **over-penalization**: the method often notices a real issue and then treats it as more decision-relevant than the official review process did.

This same pattern shows up in the 48-paper benchmark context. The system is stronger on rejected papers than on accepted papers, which is exactly what concern alignment is meant to unpack.

## Where the profile is most informative

### 1. `beyond_problem_solving` (correct rejection)

This is one of the configuration's best papers. The review aligns well with the official rejection rationale, and the strict recall is high. The case is useful because it shows that the method can identify structural issues, not only generic complaints.

### 2. `adversarial_dejavu` (correct acceptance)

This is the strongest acceptance case for the configuration in the Named Papers slice. The review recognizes the paper's core contribution and still surfaces legitimate limitations.

### 3. `rl_backtracking_feedback` and `rl_reasoning_limits` (incorrect rejections)

These are the two clearest calibration gaps. In both cases the system finds non-trivial concerns, but the official process treated those concerns as non-blocking for acceptance. That distinction is the key lesson: finding a real weakness is not the same thing as making the right decision.

## Verdict table (Named Papers slice, 9 papers)

| Paper | Decision | Verdict | Error | Strict recall | Loose recall | AI concerns |
|---|---|---|---|---|---|---|
| adversarial_dejavu | ACCEPTED | ACCEPT (6) | TP | 22.7% | 27.3% | 9 |
| artificial_hivemind | ACCEPTED | REJECT (4) | FN | 15.8% | 21.1% | 7 |
| beyond_problem_solving | REJECTED | REJECT (4) | TN | 55.6% | 55.6% | 11 |
| cmdp_meta_safe_rl | ACCEPTED | REJECT (4) | FN | 21.1% | 31.6% | 9 |
| collabllm | ACCEPTED | REJECT (5) | FN | 36.4% | 45.5% | 11 |
| from_assistant_pentest | REJECTED | REJECT (3) | TN | 30.0% | 40.0% | 11 |
| from_capabilities_pentest | ACCEPTED | REJECT (3) | FN | 40.0% | 40.0% | 13 |
| rl_backtracking_feedback | ACCEPTED | REJECT (4) | FN | 38.5% | 46.2% | 15 |
| rl_reasoning_limits | ACCEPTED | REJECT (5) | FN | 34.6% | 34.6% | 9 |

In System A · Opus, detection outpaces calibration. It often recovers a substantial share of the official concerns and is especially good at surfacing decisive blockers on rejected papers. But the method remains reject-heavy on accepted papers, indicating that it does not consistently separate "real but survivable" concerns from "paper-breaking" ones. In short: it finds many of the right problems, but often treats non-blocking concerns as rejection-worthy.
