Review outline:

**1. Significance and novelty**

This paper addresses a timely and important question in the LLM reasoning community: whether RLVR genuinely elicits new reasoning capabilities or merely reshapes the sampling distribution over patterns already present in the base model. The core finding—that base models surpass RLVR models at large pass@k values, and that RLVR reasoning paths are already within the base model's output distribution—is provocative and practically consequential for the field's research prioritization. The novelty is moderate: the use of pass@k as a reasoning boundary probe is not new (cited prior work), and individual observations (e.g., entropy collapse, pass@k degradation) have been noted in concurrent/prior work (Dang et al., DeepSeek-Math). The paper's contribution is primarily in the systematic scale and breadth of evidence (multiple model families, tasks, algorithms) and the combination of complementary analyses (coverage, perplexity, distillation contrast).

---

**2. Potential reasons for acceptance**

- Comprehensive empirical coverage: the paper spans 4+ model families, 3 task domains (math, code, vision), 6 RL algorithms, and multiple scales, lending robustness to the central claim.
- The pass@k methodology offers a principled and interpretable lens for reasoning boundary assessment, and the paper takes care to validate CoT correctness manually and address the random-guessing concern.
- The distillation vs. RLVR contrast (Section 4.2) is a clean and insightful comparison that sharpens the paper's narrative and offers actionable implications.
- The Sampling Efficiency Gap (∆SE) metric is a useful conceptual contribution for benchmarking RL algorithms against the base model upper bound.
- Clear writing and well-structured presentation with extensive supplementary material, prompt templates, and reproducibility details.

---

**3. Potential reasons for rejection**

1. **The central claim ("RLVR does not elicit new reasoning") may be overstated given the experimental design and inherent limitations of pass@k.**
   - Pass@k at realistic k values (128–1024) can only probe a finite-sample approximation of the model's true reasoning boundary. The paper acknowledges that "with astronomically large k, even uniform sampling would find the answer," but this cuts both ways: the base model's apparent coverage advantage at large k may partly reflect its higher entropy / broader but lower-quality distribution rather than genuinely superior reasoning capacity. The paper's entropy-matching experiment (Section 4.5) partially addresses this, but the RLVR model still underperforms at matched entropy on only a subset of benchmarks, and the analysis is limited to a single model/setting.
   - The paper equates "the base model can produce a correct answer in 1 out of 1024 samples" with "the base model possesses the reasoning capability." This is a philosophically and practically debatable framing. A capability that surfaces with probability ~0.1% may not reflect robust or reliable reasoning; the distinction between latent statistical coverage and genuine reasoning ability is not sufficiently discussed.

2. **Limited investigation of scaling and training compute, weakening the generality of conclusions.**
   - The controlled RL experiments (Section 4.3) train for only 150–450 steps on 2,000 problems, which is extremely small-scale relative to frontier RLVR recipes (DeepSeek-R1 trains for orders of magnitude more steps/data). The paper's conclusion that "RLVR does not expand reasoning" may be an artifact of under-training rather than a fundamental property of RLVR.
   - The Magistral-Medium experiment (Section 4.6) is presented as evidence for larger-scale models, but the base and RL model are accessed via API with undisclosed training details, model sizes, and potential confounds (e.g., multi-stage training, data contamination). The observation that "the gap narrows at large k" on AIME is weaker than "base surpasses RL"—the paper's own figures show the curves do not clearly cross for this model, undermining the universality claim.

3. **The comparison between base and RLVR models conflates multiple confounds and lacks important controls.**
   - RLVR training reduces output entropy (acknowledged in Section 4.5), which mechanically reduces pass@k at large k. The paper attempts to control for this by raising temperature, but temperature scaling is a crude proxy for the distributional shift induced by RL. A more rigorous control would involve rejection sampling or importance-weighted estimates to disentangle the entropy effect from a genuine loss of reasoning modes.
   - The base model evaluation uses the same zero-shot prompt as the RL model, but the base model was never trained with this prompt format. Performance differences could partly reflect prompt sensitivity rather than reasoning boundary differences. The paper briefly notes that base models often produce "unformatted or non-sensical responses," yet still counts correct final answers—raising questions about whether the effective sample size for meaningful reasoning is much smaller for the base model than reported.

4. **The perplexity analysis (Section 4.1) is limited in scope and does not conclusively establish that RLVR paths are a strict subset of base model paths.**
   - The analysis is conducted on only 2 randomly sampled AIME24 problems with 16 responses each, which is far too small a sample to support a general claim. The distributional overlap of perplexity values does not formally establish that every RLVR-generated reasoning path is reachable by the base model—it only shows aggregate distributional similarity.
   - Low perplexity of RLVR outputs under the base model does not rule out that RLVR produces novel *combinations* of reasoning steps or novel *orderings* that, while individually tokenwise plausible under the base model, would never be sampled as complete sequences at any realistic k. The paper does not analyze at the level of reasoning strategies or solution structures, only at the token-level likelihood.

---

**4. Suggestions for improvement**

1. **Strengthen the scaling analysis.** Train RLVR models for significantly longer (thousands of steps, larger datasets) in the controlled setup to determine whether the reasoning boundary gap is a fundamental property or a consequence of under-training. If compute is limited, at least provide learning curves of pass@k at large k as a function of training steps to characterize the trend and extrapolate.

2. **Develop a more rigorous disentanglement of entropy reduction from reasoning scope reduction.** Beyond temperature matching, consider measuring pass@k under importance-weighted sampling from the RLVR model reweighted to match the base model's distribution, or compare models with explicit entropy-preserving RL objectives (e.g., maximum entropy RL) to isolate the effect.

3. **Expand and formalize the perplexity / coverage analysis.** Scale the perplexity study to many more problems and responses. Consider measuring coverage at the level of distinct solution strategies (e.g., clustering reasoning paths) rather than only token-level perplexity, to more convincingly establish whether RLVR generates any qualitatively novel reasoning approaches.

4. **Nuance the framing and claims.** Distinguish between "RLVR does not expand the set of problems solvable at any k" and "RLVR does not introduce new reasoning strategies." The former is an empirical observation about pass@k curves; the latter is a much stronger claim that requires deeper analysis of reasoning structure. Acknowledge more explicitly that the conclusions may be specific to current training scales and may not hold under significantly scaled RLVR regimes.