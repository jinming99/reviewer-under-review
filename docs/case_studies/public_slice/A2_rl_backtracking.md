# Case Study A2: Reinforcement Learning with Backtracking Feedback

**Paper**: Reinforcement Learning with Backtracking Feedback  
**Venue outcome**: NeurIPS 2025 Poster  
**Official scores**: pre-rebuttal `[5, 4, 4, 5]`; post-rebuttal `[5, 4, 4, 5]`  
**Ground truth**: ACCEPTED

*Scope: 9-paper Named Papers case study slice.*

> *Author note. M. Jin is a co-author on this paper. It is the headline case on the public demo because it is the hardest accepted-paper case in the slice — under the pipeline headline extraction every released baseline reads as REJECT (the venue accepted), and even under the follow-up audit five of six still reject — not because of authorship. The same diagnostic claim could be made from any paper where verdict and concern-level signals diverge. Independent reanalysis is encouraged; the per-paper artifacts and the audit data for this slice (`data/audit/verdict_inference_named_9.csv`, reconciled 54-row CSV from the 9-paper audit) are public.*

> *Verdict-inference note: per-paper verdicts shown below are inferred from each system's review by our extraction pipeline (native for both System A configurations; inferred for the other four); System M reviews additionally contain coordination artifacts that make verdict inference structurally unreliable for that configuration. A follow-up audit re-read all 54 reviews in this slice with two independent raters using alternative inference rules. On this paper: pipeline 0/6 accept → audited 1/6 accept, 5/6 reject. **System L · GPT-4o's review actually reads as ACCEPT** under both independent raters (tone consensus + strong gate signal), so its audited verdict flips from the pipeline's REJECT. Five of six still reject under any reading — the paper genuinely is hard for these baselines — but the pipeline's default-REJECT rule is part of what turned "hardest" into "0/6." See the demo's Verdict Sensitivity panel (Named Papers segment) for the full per-system breakdown.*

Under the pipeline headline extraction, this is the hardest accepted paper in the Named Papers slice: all six baselines are read as REJECT. Under the follow-up audit, that softens to 1/6 ACCEPT and 5/6 REJECT (System L · GPT-4o's review reads as ACCEPT under both independent raters), but the paper remains a strong stress test for concern-level calibration. The official record contains real concerns, but none of them are marked decisive, and the venue still accepted the paper as a poster.

## The official record

The official record lists thirteen items spanning reproducibility, safety-critic validation, adaptive-attack robustness, efficiency measurement, baseline contextualization, reward-design justification, figure clarity, and placeholder references. Five are marked major (O1–O5), five moderate (O6–O9, O12), and three minor (O10, O11, O13). Importantly, every single one is marked **non-decisive** on the released official record, and most are recorded as resolved in rebuttal.

The five major concerns drive most of the substantive discussion:

- **O1** (major, resolved, non-decisive): Key implementation details (data splits, prompt sampling, training hyperparameters, compute budget) are deferred to supplementary, making reproducibility difficult from the main text alone.
- **O2** (major, resolved, non-decisive): Section 4.2 names a 'single, powerful LLM-based safety critic' but omits evaluation of critic quality, making it hard to assess whether critic quality or policy learning drives the performance gains.
- **O3** (major, resolved, non-decisive): The method relies on a single LLM safety critic, which can be vulnerable to adversarial attacks or otherwise produce incorrect judgments.
- **O4** (major, resolved, non-decisive): The evaluation set includes GCG and decoding-parameter variants but does not target RLBF's specific backtracking signal, leaving robustness under truly adaptive adversaries unclear.
- **O5** (major, resolved, non-decisive): A core claim is higher efficiency relative to BSAFE, yet experiments only report ASR and utility, not metrics like average tokens discarded or latency under backtracking.

An additional moderate item is worth naming because multiple baselines echo it:

- **O6** (moderate, resolved, non-decisive): The paper does not contextualize ASR numbers with non-backtracking methods that improve safety via post-training or at inference time.

A concise way to describe the official record is: real methodological concerns spanning thirteen items, but no recorded blocker severe enough to force rejection.

## How the released baselines handled it

*Scope: 9-paper Named Papers case study slice — per-paper recall on this single paper.*

| Method | Verdict | Error type | Strict recall | Loose recall | AI concerns |
|---|---|---|---|---|---|
| System A · Opus | REJECT (4) | FN | 38.5% | 46.2% | 15 |
| System A · GPT-4o | REJECT (4) | FN | 7.7% | 30.8% | 7 |
| System L · Opus | REJECT | FN | 30.8% | 38.5% | 8 |
| System L · GPT-4o | REJECT | FN | 7.7% | 7.7% | 4 |
| System M · GPT-4o | REJECT | FN | 53.8% | 69.2% | 15 |
| System O · Opus | REJECT | FN | 30.8% | 61.5% | 24 |

Recall is computed against all 13 official concerns.

### What stands out

- `System M · GPT-4o` has the highest strict recall in this case, yet still rejects.
- `System A · Opus`, `System L · Opus`, and `System O · Opus` all raise serious-looking but familiar concerns about novelty, reproducibility, and robustness.
- The shared pattern is therefore not simple blindness. It is the decision rule that turns those concerns into a rejection.

## The common baseline story

Across the released systems, three complaints recur:

1. **Incremental novelty over earlier backtracking work**
2. **Weak statistical reporting** such as missing error bars or confidence intervals
3. **Unvalidated safety critic and robustness concerns**

Those are not fabricated concerns. They overlap the official record. The disagreement is about how much they should matter for a poster-level acceptance.

## What this case shows

This paper is a good example of workflow-level alignment rather than simple verdict prediction. A system can notice genuine weaknesses and still misread the review situation if it cannot distinguish between:

- a concern that should be fixed in revision, and
- a concern that should block acceptance outright.

Reinforcement Learning with Backtracking Feedback is the hardest accepted paper in the Named Papers slice. Under the pipeline headline extraction, all six released baselines reject it, even though the official record contains no decisive blocker across its thirteen items. Under the follow-up audit, that softens to five rejects and one accept. The baselines are not simply overlooking the paper's weaknesses; several recover substantial portions of the record. The concern-level evidence suggests that severity calibration is a major part of the error for several systems — real limitations are being treated as rejection-worthy when the venue treated them as non-blocking for a poster acceptance — but it is not the only explanation, and L · GPT-4o's audited ACCEPT shows that the verdict outcome itself depends on how tone is read.
