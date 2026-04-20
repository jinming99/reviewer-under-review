# Case Study A1: Adversarial Deja Vu

**Paper**: Adversarial Deja Vu: Jailbreak Dictionary Learning for Stronger Generalization to Unseen Attacks
**Venue**: ICLR 2026 (Poster)
**Scores**: 6 / 2 to 6 / 8 / 6 (Q4KG revised from 2 to 6 post rebuttal)
**Ground Truth**: ACCEPTED

> *Verdict-inference note: per-paper verdicts shown below are inferred from each system's review by our extraction pipeline (native for both System A configurations; inferred for the other four); System M reviews additionally contain coordination artifacts that make verdict inference structurally unreliable for that configuration. A follow-up audit re-read all 54 reviews in this slice with two independent raters using alternative inference rules. On this paper: pipeline 3/6 accept → audited 2/6 accept, 3/6 reject, 1 UNRELIABLE (System M's multi-agent coordination artifacts). The pipeline's accept count drops by one because System M's verdict cannot be reliably inferred under any method. See the demo's Verdict Sensitivity panel (Named Papers segment) for the full per-system breakdown.*

This paper tests whether automated reviewers can recognize a novel hypothesis (jailbreaks as skill recombinations) while correctly scoping a methodological concern (GPT-4.1 used as both extractor and judge) to the specific claim it affects.

---

## The Core Review Challenge

The paper has 22 official concerns, the largest count in this set, but zero decisive blockers. All major concerns were resolved in rebuttal. The central calibration question is whether a circularity concern in the explainability evaluation should be weighted as fatal to the paper or scoped to the single table where it applies.

Key structural points in the submission:

- GPT-4.1 extracts and judges skills in the explainability evaluation (Table 1). This is an LLM-evaluates-LLM loop.
- The defense results (Tables 2 to 4) use independent StrongReject evaluation, so they are not affected by the circularity.
- Figure 5 isolates the coverage mechanism at fixed data volume, showing that skill-space coverage, not data quantity, is the lever for robustness.
- Cross-model evaluation reports ASCoT achieving 2-4x lower harmfulness on unseen attacks (0.07 to 0.12 vs 0.15 to 0.42) across LLaMA-3.1-8B, Zephyr-7B, and Mistral-7B.

The official reviewers reached a resolution through rebuttal. Q4KG's initial score-2 was driven by overlap with AutoDAN-Turbo (O4/O7), not the circularity per se. After the rebuttal added a direct comparative experiment (ASCoT 0.11 vs AutoDAN-Turbo-trained 0.20 on PAIR), Q4KG revised to 6: "I am now convinced the contribution is not incremental."

---

## How Baselines Handled the Paper

Observational notes on the published baseline reviewers (raw outputs in `data/reviews/public_slice/`):

- **AI Scientist (Claude and GPT-4o runs)**: Generally flags the circularity concern around GPT-4.1 serving as both extractor and judge. Does not consistently separate this from the defense results, so verdict calibration varies by run.
- **Liang et al. (Claude and GPT-4o runs)**: Produces a very low concern count. Does not surface the coverage dividend argument as an acceptance anchor.
- **OAR**: Raises a broader concern list including experimental controls and baseline selection.
- **MARG (GPT-4o)**: Produces a high-volume concern list. Breadth is high but severity assignment is flat, so circularity and minor presentation issues tend to land at similar weight.

---

## What This Paper Reveals About Baseline Behavior

A system that treats all concerns as equally weighty will reject this paper on the circularity concern alone. The correct response requires three moves: detect the circularity, scope it to the explainability evaluation rather than the defense results, and recognize the coverage dividend experiment as independent evidence. The baselines evaluated on this paper diverge on severity scoping more than on detection. Several surface the circularity, but fewer distinguish "affects Table 1" from "affects the acceptance case."
