# Baseline Profile: System M · GPT-4o

**Method family**: MARG
**Released configuration**: GPT-4o
**Public framing**: **broad coverage; verdict inference is unreliable for this configuration**

> **Verdict-inference scope.** Verdict accuracy in this profile is inferred from review tone or structure by our extraction pipeline. Both System A configurations (Opus and GPT-4o) emit a native Decision field; this profile is not one of them. **All 48 System M reviews additionally contain multi-agent coordination artifacts (e.g., inter-agent messages, repeated draft fragments) that make verdict inference unreliable regardless of method.** Accepted-paper accuracy varies widely under alternative inference methods. Both the 9-paper Named Papers table and the 48-paper benchmark table on this page are **single run (run 1)**; the homepage displays 3-run means and will not numerically match. The same caveat applies to the per-paper verdict table and any verdict prose later on this page. The paper appendix's sensitivity audit (covering a separate 48-paper safety/alignment benchmark) shows verdict-level numbers vary with inference method, while concern-level metrics — recall, FDR, decisive precision, phantom rates — do not. The audit has since been extended to the 9-paper public slice. System M · GPT-4o's final (audited) verdict differs from its pipeline verdict on **7 of 9 papers** — in every case, the final verdict is UNRELIABLE. The multi-agent coordination artifacts that made verdict inference unreliable on the 48-paper benchmark are present on the public slice too. The per-paper verdict column on this page should be read as "the pipeline produced X, but the audit could not reliably extract a verdict from the underlying review."

### Named Papers slice (9 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 44.4% |
| TP/TN/FP/FN | 3/1/1/4 |
| Recall (strict) | 33.0% |
| Recall (loose) | 43.9% |
| Precision | 57.6% |
| Phantom rate | 42.4% |
| Decisive recall | 29.2% |

### Full benchmark context (48 papers)

| Metric | Value |
|---|---|
| Verdict accuracy | 56.2% |
| Accepted-paper accuracy | 58.3% |
| Rejected-paper accuracy | 54.2% |
| Average strict recall | 31.4% |
| Average phantom rate | 60.1% |


## Behavioral profile

The two layers of System M · GPT-4o's behavior have to be read separately.

**Concern coverage (stable across inference methods).** The system covers a broad range of official concerns and has the highest loose recall in the Named Papers slice. Strict recall in the 48-paper benchmark is 31.4% and phantom rate is 60.1%. These concern-level metrics are computed directly from the multi-agent transcripts and do not depend on how a verdict is inferred from the review.

**Verdict (unstable, structurally unreliable).** All 48 System M reviews contain multi-agent coordination artifacts — inter-agent messages, repeated draft fragments, and other state that the review text was never meant to commit to a binary recommendation. Whichever inference method is applied, the resulting verdict is reading more about the artifact than about the system's intended recommendation. The accepted-paper accuracy in the tables above (58.3% on the 48-paper benchmark, 44.4% on the 9-paper slice, both single-run) reflects our extraction pipeline's reading; under alternative inference methods this figure ranges widely. Comparisons that lean on M's verdict accuracy — including statements about "lenient thresholds," "acceptance-friendly behavior," or threshold contrasts with the reject-heavy systems — are not supported by the data.

The diagnostic value of this profile is in the concern-level surface, not in the verdict.

## Where the profile is most informative

The cases below are diagnostic for **concern coverage and overlap** with official concerns. They are not diagnostic for the system's intended verdict, because the verdict shown for each case is itself inferred from a structurally unreliable transcript.

### 1. `from_assistant_pentest`

System M's review covers a substantial share of the official concerns on a paper that was rejected by the venue. The verdict our pipeline extracts lands on the acceptance side, but because the underlying review text contains coordination artifacts, this is a thresholding observation about the inference method, not about the system's calibration. The case is useful as a concern-coverage exemplar.

### 2. `from_capabilities_pentest`

The system covers a large share of the official concerns on the borderline accepted revision in this paper pair. Concern overlap is the diagnostic signal here; the verdict is again subject to the structural-artifact caveat above.

### 3. `rl_backtracking_feedback`

Strict recall on this paper is high, illustrating broad concern coverage even when the venue's decision and the inferred verdict diverge. As with the other cases, the divergence cannot be attributed to a calibration choice by the system without first resolving the verdict-inference issue.

## Nine-paper verdict table

| Paper | Decision | Verdict | Error | Strict recall | Loose recall | AI concerns |
|---|---|---|---|---|---|---|
| adversarial_dejavu | ACCEPTED | ACCEPT | TP | 18.2% | 27.3% | 10 |
| artificial_hivemind | ACCEPTED | REJECT | FN | 21.1% | 31.6% | 9 |
| beyond_problem_solving | REJECTED | REJECT | TN | 33.3% | 44.4% | 9 |
| cmdp_meta_safe_rl | ACCEPTED | REJECT | FN | 26.3% | 42.1% | 9 |
| collabllm | ACCEPTED | ACCEPT | TP | 22.7% | 27.3% | 10 |
| from_assistant_pentest | REJECTED | ACCEPT | FP | 50.0% | 60.0% | 11 |
| from_capabilities_pentest | ACCEPTED | ACCEPT | TP | 60.0% | 70.0% | 10 |
| rl_backtracking_feedback | ACCEPTED | REJECT | FN | 53.8% | 69.2% | 15 |
| rl_reasoning_limits | ACCEPTED | REJECT | FN | 11.5% | 23.1% | 9 |
