# Case Study E3: RL Reasoning Limits

**Paper**: Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?  
**Venue outcome**: NeurIPS 2025 — Best Paper Runner-up (Oral)  
**Official scores**: pre-rebuttal `[5, 6, 5, 5]`; post-rebuttal `[6, 6, 6, 6]`  
**Ground truth**: ACCEPTED

> *Verdict-inference note: per-paper verdicts shown below are inferred from each system's review by our extraction pipeline (native for both System A configurations; inferred for the other four); System M reviews additionally contain coordination artifacts that make verdict inference structurally unreliable for that configuration. A follow-up audit re-read all 54 reviews in this slice with two independent raters using alternative inference rules. On this paper: pipeline 1/6 accept → audited 1/6 accept, 4/6 reject, 1 UNRELIABLE (System M). The accept count holds; the only flip is System M's verdict becoming UNRELIABLE because of coordination artifacts in its review text. See the demo's Verdict Sensitivity panel (Named Papers segment) for the full per-system breakdown.*

**Scope**: measurement / negative-result paper on RLVR and base-model reasoning capacity.

This measurement paper reports a negative result on a timely question: RLVR does not expand reasoning capacity beyond what is already present in the base model, supported by broad evidence across six algorithms and three task domains. The AC wrote that the paper is "masterfully executed" and that the rebuttal "essentially addresses all reviewers' concerns," noting a perfect post-rebuttal score profile and unanimous strong acceptance. Five of six released baseline configurations land on reject on the same paper.

## The official record

The official concerns push on scale, alternative explanations, and presentation clarity:

- **O1** (major, resolved, non-decisive): Results are all on relatively small models (7-32B parameters) and low training data diversity (mathematical reasoning on GSM8K + MATH, coding on LeetCode and TACO); quite far from RLVR-trained frontier systems. Both model size and training data can significantly change properties of models.
- **O2** (moderate, resolved, non-decisive): The random guessing explanation needs stronger control: low percentage of problems with at least one correct CoT in 8-25 samples is a good sanity check but a low bar. Should report percentage of trajectories containing flawed CoTs and use larger samples with LLM-as-judge to bound performance attributable to random guessing.
- **O3** (moderate, resolved, non-decisive): Overfitting to the test set is another alternative explanation not addressed. Distillation and train vs test results should indicate overfitting, but this connection is not made explicit.
- **O4** (minor, resolved, non-decisive): Table 1 should show training data information, not just test sets.
- **O5** (minor, resolved, non-decisive): Figure 6 should add a sentence on the relevance of comparing perplexity to o1 responses.
- **O6** (minor, resolved, non-decisive): Figure 8 is hard to read with folded y-axis; should perhaps show only k@1 and k@256 or use delta notation.

Those are serious concerns, but the official record still converges to unanimous post-rebuttal support. The venue judged the empirical and analytical contribution to be strong enough.

## How the released baselines handled it

| Method | Verdict | Error type | Strict recall | Loose recall | AI concerns |
|---|---|---|---|---|---|
| System A · Opus | REJECT (5) | FN | 34.6% | 34.6% | 9 |
| System A · GPT-4o | REJECT (3) | FN | 11.5% | 11.5% | 4 |
| System L · Opus | REJECT | FN | 19.2% | 23.1% | 8 |
| System L · GPT-4o | ACCEPT | TP | 23.1% | 23.1% | 5 |
| System M · GPT-4o | REJECT | FN | 11.5% | 23.1% | 9 |
| System O · Opus | REJECT | FN | 3.9% | 7.7% | 6 |

### What stands out

- `System L · GPT-4o` is the only accepting configuration in the released slice.
- The rejecting systems often describe the finding as unsurprising, insufficiently novel, or lacking actionable solutions.
- That is a readable divergence in contribution-type weighting: the community treated a rigorous negative result as the paper's contribution, while several automated reviewers treated the same finding as a weakness.

## What this case shows

If AI reviewers are going to be part of scientific workflows, they need to read **measurement, diagnosis, and negative-result papers** the same way the community does when deciding the paper's value. The official record moves to unanimous support after rebuttal and an AC who calls the paper "masterfully executed," yet five of six released configurations still reject. The common pattern across those rejects is novelty-weighting — systems weight "confirms an important limitation with broad evidence" lower than the venue did.
