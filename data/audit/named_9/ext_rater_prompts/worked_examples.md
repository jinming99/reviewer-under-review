# Worked Examples from 20-Paper Audit

These examples show how to apply both tone and gate methods. They are drawn from the first 20-paper batch you already completed and represent the key patterns to watch for.

---

## Example 1: Clear REJECT (all methods agree)

**Paper**: agentmisalignment_measuring_propensity_misaligned
**System**: A (Opus) | **Official decision**: REJECTED

**Review tone**: Highly critical. Identifies fundamental methodology concerns, questions whether the benchmark actually measures misalignment vs. gaming. Multiple "major" concerns about evaluation validity.

**Tone verdict**: REJECT (high confidence)
**Signal**: Review identifies fundamental validity concerns about the core measurement.

**Gate classification**: 4 major concerns map to fundamental gates:
- A1 (major): "Benchmark design allows agents to succeed through gaming rather than alignment" → **G4** (validity bug)
- A2 (major): "No comparison to existing alignment benchmarks" → **G2** (baseline fairness)
- A3 (major): "Claims about misalignment not supported by the evaluation" → **G1** (claim-evidence mismatch)
- A4 (major): "Metric conflates task completion with alignment" → **G4** (validity bug)

**Gate verdict**: REJECT (4 fundamental hits)

---

## Example 2: Clear ACCEPT (all methods agree)

**Paper**: aria_training_language_agents_intention-driven
**System**: L (GPT-4o) | **Official decision**: ACCEPTED (Spotlight)

**Review tone**: Positive and constructive. Praises the conceptual framework, notes broad evaluation. Concerns are moderate (scope could be broader, some implementation details missing) but none framed as blocking.

**Tone verdict**: ACCEPT (medium confidence)
**Signal**: Constructive tone, concerns are addressable, no blocking-level criticism.

**Gate classification**: 0 major/fatal concerns → 0 fundamental gate hits. All concerns are moderate severity.

**Gate verdict**: ACCEPT (0 fundamental hits + positive acceptance signal in decision_drivers)

---

## Example 3: Positive Tone, Missed Flaws (tone=ACCEPT, gate=REJECT)

**Paper**: ctrl-alt-deceit_sabotage_evaluations_automated_ai
**System**: L (Opus) | **Official decision**: ACCEPTED (Spotlight)

**Review tone**: Balanced. Lists strong positive reasons (novel evaluation framework, practical relevance). Also lists several analytical concerns, but they're interspersed with acknowledgment of the contribution.

**Tone verdict**: ACCEPT (low confidence)
**Signal**: Despite listing concerns, the review's accept-reasons section is substantive and the overall framing is appreciative.

**Gate classification**: The concerns include 15 major/fatal items hitting fundamental gates:
- Multiple concerns about claim-evidence gaps → G1
- Concerns about evaluation validity (whether sabotage tasks measure what's claimed) → G4
- Concerns about baseline fairness → G2

**Gate verdict**: REJECT (15 fundamental hits)

**Why they diverge**: This is the classic "Opus depth-penalty" pattern. L (Opus) writes analytically rich reviews that engage deeply with the work, producing many technically grounded concerns. The tone is balanced because the reviewer genuinely appreciates the work, but the concern count is high because the reviewer also identifies many issues. The gate framework treats all major concerns equally regardless of tone; the tone method captures the reviewer's overall assessment.

**This divergence is informative, not an error.** It shows that verdict inference method matters.

---

## Example 4: Structurally Unreliable (System M)

**Paper**: agentmisalignment_measuring_propensity_misaligned
**System**: M (GPT-4o) | **Official decision**: REJECTED

**Review tone**: Contains multi-agent coordination artifacts ("SEND MESSAGE: Agent 13..."), repeated draft fragments, meta-commentary about the review process. Where substantive text exists, it tends to be positive.

**Tone verdict**: REJECT (low confidence) — forced binary label; output is structurally unreliable.
**Signal**: Review is structurally broken; verdict from this review is not meaningful.

**Gate classification**: Despite structural issues, 11 concerns were extracted. 2 major concerns map to fundamental gates (G4, G5).

**Gate verdict**: REJECT (2 fundamental hits)

**Flag**: `structural_unreliable_flag = YES`

**Note**: All System M reviews should be evaluated for structural unreliability. If the review text contains agent coordination artifacts, repeated fragments, or lacks coherent structure, flag it. Still assign tone and gate verdicts, but the structural flag tells downstream analysis to treat these with caution.

---

## Example 5: System A with Native Verdict

**Paper**: infinity_beyond_tool-use_unlocks_length
**System**: A (Opus) | **Official decision**: ACCEPTED (Oral)

**Review text includes**: An explicit `Decision: Reject` field in the structured JSON output.

**Tone verdict**: REJECT (high confidence) — the review contains an explicit decision field.
**Signal**: Native `Decision: Reject` in review output.

**Gate classification**: 5 major concerns:
- A1: "Core theoretical results have limited novelty — pigeonhole argument" → G5 (novelty)
- A2: "Theory-practice gap — learning algorithm uses string-matching, not gradient descent" → G1 (claim-evidence)
- A3: "Best-of-10-seeds reporting instead of aggregated statistics" → G6 (cherry-picking)
- A4: "Transformer baselines relatively small, don't incorporate known length-gen techniques" → G2 (baseline fairness)
- A5: "No comparison of tool-augmented SSMs vs tool-augmented Transformers" → G2 (baseline fairness)

**Gate verdict**: REJECT (4 fundamental hits: G1, G2, G5)

**Note**: For System A, the pipeline verdict matches the native Decision field. The gate verdict is computed independently from the concern content. Both happen to agree (REJECT) here.

---

## Example 6: GPT-4o Positive Tone Reflects Capability Gap

**Paper**: decoupling_safety_into_orthogonal_subspace
**System**: L (GPT-4o) | **Official decision**: REJECTED

**Review tone**: Positive. Calls the theoretical framework "well-structured" and praises "extensive empirical evidence." No blocking-level criticism detected.

**Tone verdict**: ACCEPT (medium confidence)
**Signal**: Positive framing throughout; concerns are presented as addressable.

**Gate classification**: Concerns are moderate severity (theoretical complexity, limited scope). 0 fundamental gate hits — because GPT-4o missed the paper's actual fatal flaw.

**Gate verdict**: ACCEPT (0 fundamental hits + positive signal)

**What was missed**: The Opus review of the same paper identifies a dimensional inconsistency in the SVD derivation, a mathematical tautology presented as a discovery, and a missing mechanism explanation — all fatal-level concerns that GPT-4o's review completely overlooks.

**Flag**: `positive_tone_missed_flaws_flag = YES`

**Lesson**: This review sounds positive because it fails to identify the paper's real problems, not because the paper is strong. The tone verdict (ACCEPT) and gate verdict (ACCEPT) are both wrong — they agree, but both are wrong for the same reason (shallow analysis). This pattern is common in GPT-4o reviews and should be flagged when detected.
