# Summary

This paper introduces Reinforcement Learning with Backtracking Feedback (RLBF), a framework for improving LLM safety by enabling models to dynamically detect and correct safety violations during generation. RLBF extends prior work (BSAFE) with three components: (1) a simplified backtracking mechanism using a 'backtrack by x tokens' signal instead of repeat-and-edit procedures, (2) an improved SFT data generation method (BSAFE+) that injects violations into coherent safe text to create more realistic training examples, and (3) an RL stage using GRPO with LLM critic feedback that trains the model on its own generation distribution. Experiments on Gemma 2 and LLaMA 3 models across multiple attack types (Middle Filling, GCG, Decoding Parameter manipulation) show significant reductions in attack success rates while preserving utility on MMLU, BBH, GSM8K, and MATH benchmarks.
# Strengths

- The problem of robust LLM safety beyond shallow alignment is important and well-motivated. The observation that standard safety training creates brittle refusal mechanisms is well-supported by cited prior work.
- The 'backtrack by x tokens' mechanism is a sensible simplification over BSAFE's repeat-and-edit approach, avoiding regeneration of harmful content and reducing potential artifacts.
- The BSAFE+ data generation strategy is well-reasoned: injecting violations into the model's own safe responses ensures in-distribution continuations and preserves answer quality (49.4% vs 50.6% win rate compared to BSAFE's 28.2% vs 71.8%).
- RLBF shows a clear advantage over BSAFE+ on standard LMSYS harmful queries (1-2% ASR vs 14-17%), suggesting the RL stage provides genuine value beyond SFT-based correction alone.
- Utility preservation is strong across four benchmarks (MMLU, BBH, GSM8K, MATH), with negligible degradation compared to IT baselines.
- The ablation study in Table 5 effectively isolates the contribution of the backtracking mechanism, showing that mid-generation backtracking is particularly important (7% ASR without vs 1% with full RLBF).

# Weaknesses

- The contribution is substantially incremental over BSAFE (Sel et al., 2025b). The core idea of backtracking for safety already exists; the main additions are a simpler token format, better data generation, and standard RL fine-tuning. The conceptual novelty is limited.
- The paper repeatedly references 'supplementary material' for critical experimental details (hyperparameters, training specifics, compute resources, data generation process) but no supplementary material is included in the submission. This renders the experimental claims largely unverifiable and makes reproduction impossible.
- The original BSAFE method is never directly compared against in experiments — only the authors' own BSAFE+ variant appears. Similarly, the Reset approaches (Qi et al., 2025; Zhang et al., 2025) are discussed extensively in Section 3 but excluded from all experimental tables. This makes it impossible to assess the true marginal contribution over existing methods.
- Table 4's attack prevention rates are all exact multiples of 0.02, strongly suggesting only ~50 samples per safety category. Such a small evaluation set undermines the reliability of per-category claims.
- There is no evaluation of the LLM safety critic — no accuracy metrics, false positive/negative rates, or analysis of how critic errors propagate to the trained model. The entire framework hinges on this component, yet it is treated as a perfect black box.
- Table 2 does not specify which model size or configuration is evaluated for GCG and Decoding Parameter attacks, making these results difficult to interpret or contextualize.
- The GRPO implementation is underspecified. Section 4.2.3 vaguely mentions penalizing known violating patterns 'by adding constraints or penalty terms to the GRPO update step' without concrete algorithmic details. The RL contribution — supposedly the paper's primary novelty — lacks the precision needed for evaluation or reproduction.
- Despite claiming efficiency improvements over BSAFE, no latency measurements, throughput comparisons, or computational overhead analysis is provided.
- No statistical significance analysis or error bars are reported. When BSAFE+ and RLBF show similar ASRs on LMSYS-MF (e.g., both 3-7%), it is unclear whether differences are meaningful.
- No analysis of adaptive attacks where adversaries are aware of the backtracking mechanism is provided. Robustness to mechanism-aware adversaries is critical for evaluating a safety method.
- The reward function values (-1.0, +1.0, -0.5, -0.2) appear ad hoc with no justification or ablation study on their sensitivity.

# Questions

- Which model size and configuration was used for the experiments in Table 2 (GCG and Decoding Parameter attacks)?
- How many samples per safety category were used in Table 4? The fact that all values are multiples of 0.02 suggests ~50, which seems insufficient for reliable per-category conclusions.
- What LLM is used as the safety critic? What is its accuracy on detecting safety violations, and what are its false positive and false negative rates?
- Can you provide direct comparisons with the original BSAFE method and the Reset approaches (Qi et al., 2025; Zhang et al., 2025)?
- What happens under adaptive attacks where the adversary knows about the backtracking mechanism and specifically tries to circumvent it (e.g., crafting violations the critic misses, or exploiting the backtrack token vocabulary)?
- What is the actual computational overhead of RLBF at inference time compared to standard generation and compared to BSAFE?
- How sensitive are the results to the specific reward function values (-1.0, +1.0, -0.5, -0.2)?
- Can you provide the concrete algorithmic details for how known violating patterns are penalized during the GRPO update step, as mentioned in Section 4.2.3?
- The supplementary material with experimental details is referenced repeatedly but not included. Can you provide the missing hyperparameters, training configurations, and data generation specifics?

# Limitations

- The limitations section is superficial, mentioning computational demands and difficulty defining harmful content without quantifying either concern.
- No discussion of the critic as a single point of failure — if the critic is biased or inaccurate, the entire framework could learn incorrect backtracking behavior or miss genuine violations.
- No analysis of how cascading backtracks in long-form generation could degrade output quality or coherence.
- No discussion of the risk that backtracking tokens could be adversarially triggered to suppress legitimate content (over-censorship via false positive backtracking).
- No analysis of potential negative societal impact from the red-teaming data generation process.

# Scores

- **Originality**: 2
- **Quality**: 2
- **Clarity**: 2
- **Significance**: 2
- **Soundness**: 2
- **Presentation**: 2
- **Contribution**: 2
- **Overall**: 4
- **Confidence**: 4

# Decision: Reject