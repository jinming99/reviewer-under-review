# Baseline Profile: System O · Opus

**Method family**: OAR  
**Configuration**: Opus  
**Profile**: **technical auditor, weak decision alignment**

> **Verdict-inference scope.** Verdict accuracy in this profile is inferred from review tone or structure by our extraction pipeline. Both System A configurations (Opus and GPT-4o) emit a native Decision field; this profile is not one of them. Both the 9-paper Named Papers table and the 48-paper benchmark table on this page are **single run (run 1)**; the homepage displays 3-run means and will not numerically match. The same caveat applies to per-paper verdict tables and any verdict prose later on this page. The paper appendix's sensitivity audit (covering a separate 48-paper safety/alignment benchmark) shows verdict-level numbers vary with inference method, while concern-level metrics — recall, FDR, decisive precision, phantom rates — do not. The audit has since been extended to the 9-paper public slice. System O · Opus's final (audited) verdict differs from its pipeline verdict on 1 of 9 papers: on `collabllm`, the pipeline ACCEPT flips to REJECT after human adjudication — one rater caught specific technical errors (inflated headline, contradictory figure, incorrect causal derivation) that the pipeline minimized. This matches its 48-paper pattern: mostly method-stable, with occasional volatility on papers where the AI review contains precise-but-easily-minimized technical errors.

### Named-paper slice (9 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 44.4% |
| TP/TN/FP/FN | 2/2/0/5 |
| Recall (strict) | 13.2% |
| Recall (loose) | 27.7% |
| Precision | 28.6% |
| Phantom rate | 71.4% |
| Decisive recall | 0.0% |

### Full benchmark context (48 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 54.2% |
| Accepted-paper accuracy | 29.2% |
| Rejected-paper accuracy | 79.2% |
| Average strict recall | 13.9% |
| Average phantom rate | 79.8% |


## Behavioral profile

System O · Opus shows a pattern of adding value at one level of the review process while remaining weak at another. Its reviews often contain precise technical observations, numerical spot-checks, and local consistency checks. But the concern-alignment metrics show that those observations often land on a different stratum from the concerns that drove the official decisions.

That combination is what makes this profile informative. It illustrates that review usefulness is multi-dimensional: technical auditing and decision calibration are related, but not the same skill.

## Where the profile is most informative

### 1. `collabllm` and `artificial_hivemind` (correct acceptances with low strict recall)

These cases show that the method can still land on the correct side of the decision even when it recovers only a small fraction of the official concern set. That is useful evidence that verdict agreement alone can flatter a method.

### 2. `from_capabilities_pentest` (high recall, wrong verdict)

This case demonstrates that abundant critique does not guarantee correct calibration. The method surfaces many issues and still rejects a paper that the venue accepted.

### 3. `beyond_problem_solving` (correct rejection, different focus)

This case is important because the method is directionally correct but still focuses on a different layer of critique than the official decision drivers. It is a clean L4 attention-profile example.

## Nine-paper verdict table

| Paper | Decision | Verdict | Error | Strict recall | Loose recall | AI concerns |
|---|---|---|---|---|---|---|
| adversarial_dejavu | ACCEPTED | REJECT | FN | 4.5% | 13.6% | 9 |
| artificial_hivemind | ACCEPTED | ACCEPT | TP | 5.3% | 10.5% | 5 |
| beyond_problem_solving | REJECTED | REJECT | TN | 0.0% | 22.2% | 10 |
| cmdp_meta_safe_rl | ACCEPTED | REJECT | FN | 0.0% | 10.5% | 8 |
| collabllm | ACCEPTED | ACCEPT | TP | 4.5% | 22.7% | 6 |
| from_assistant_pentest | REJECTED | REJECT | TN | 20.0% | 40.0% | 26 |
| from_capabilities_pentest | ACCEPTED | REJECT | FN | 50.0% | 60.0% | 39 |
| rl_backtracking_feedback | ACCEPTED | REJECT | FN | 30.8% | 61.5% | 24 |
| rl_reasoning_limits | ACCEPTED | REJECT | FN | 3.9% | 7.7% | 6 |

## Summary

System O · Opus is best understood as a technical auditing configuration. It can produce specific, locally valuable checks, but the metrics show weak alignment with the official decision-driving concerns and the highest phantom rate among the six configurations in this profile set. It reads as a useful complement in a workflow, but a weak stand-alone proxy for final review judgment. In short: strong at technical spot-checking, often focused on a different stratum of concerns than what drove the decision.
