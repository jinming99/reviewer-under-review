# Summary

COLLABLLM is a training framework for making LLMs more collaborative in multiturn interactions. The core idea is the Multiturn-aware Reward (MR), which uses forward simulation—sampling future conversation turns via an LLM-based user simulator—to estimate the long-term impact of a model response. The conversation-level reward combines extrinsic (task performance) and intrinsic (efficiency, LLM-judged interactivity) components. The framework supports offline (SFT, DPO) and online (PPO, Online DPO) training via RL. Three multiturn benchmarks are introduced: MediumDocEdit-Chat (document editing), BigCodeBench-Chat (coding), and MATH-Chat (math QA). Experiments on Llama-3.1-8B show improvements over the base model and a proactive prompting variant. A 201-person user study on document writing demonstrates increased user satisfaction (+17.6%) and reduced time (-10.4%).
# Strengths

- Addresses an important and practical problem: training LLMs for active multiturn collaboration rather than passive single-turn response generation. The motivation is well-articulated with concrete examples (Figure 2).
- The framework is conceptually clean and general. The MR formulation naturally combines forward simulation with a decomposed reward (extrinsic + intrinsic), and the approach is agnostic to the specific RL algorithm (PPO, DPO).
- Large-scale user study with 201 MTurk participants provides genuine real-world validation. The longitudinal interaction ratings (Figure 7d) showing COLLABLLM's sustained engagement versus the Base model's declining trajectory are particularly compelling.
- Thorough ablation study (Section 5.1, Figure 9) systematically varies reward components and forward window sizes, clearly demonstrating the benefit of forward-looking rewards over immediate reward variants.
- Clear and well-organized writing with informative figures. The case study analysis (Figures 5-6) concretely illustrates how different reward mechanisms distinguish collaborative from passive responses.
- Safety evaluation (Appendix C) demonstrates that collaborative training does not degrade the base model's safety alignment, and the impact statement thoughtfully discusses societal implications.

# Weaknesses

- Critical absence of empirical comparisons with existing multiturn training methods. The paper discusses MTPO (Shani et al., 2024), STaR-GATE (Andukuri et al., 2024), ARCHER (Zhou et al., 2024), and others in related work, and compares them conceptually in Table 4, yet provides no experimental comparison with any of them. The only baselines are vanilla Llama-3.1-8B and a prompting variant, which is insufficient for a top venue.
- No ablation isolating the MR contribution from the effect of multiturn training data. All COLLABLLM variants in Table 1 are trained on MR-guided data (where responses are selected/ranked by MR scores). A baseline trained on equivalent multiturn conversation data generated without MR ranking is needed to attribute gains to the forward-simulation reward itself. Additionally, GPT-4o is used as the assistant LLM for synthetic data generation (Appendix B.1), meaning training data quality is partly inherited from a much stronger model.
- Evaluation circularity: The intrinsic reward RLLM(t) uses an LLM judge during training, and the primary evaluation metric ITR is also scored by an LLM judge (Claude-3.5-Sonnet). The model is partially trained to produce what LLM judges reward, then evaluated by LLM judges. While the user study mitigates this for satisfaction, the ITR metric—which shows the largest gains (46.3%)—remains affected by this circularity.
- Absolute performance levels are low, making large relative improvements potentially misleading. MATH-Chat accuracy is 16.5%, BLEU for MediumDocEdit is 36.8%, and BigCodeBench pass rate is 13.0%. The headline '18.5% average improvement' is computed as relative gain over already-low baselines.
- No error bars, confidence intervals, or statistical significance tests reported for either simulated experiments or the user study. With small test sets (100 for MediumDocEdit, 200 for MATH), variance may be substantial.
- The causal inference framing (Appendix A) is overclaimed. Equation 5 is standard conditional expectation, not a front-door adjustment (which requires a specific graphical structure to bypass confounding). The claimed distinction from MTPO in Appendix A.2 is also overstated—both approaches estimate expected future reward; the difference is in sampling strategy, not observational vs. interventional identification.
- Generalization evidence (Table 2) is mixed. On Abg-CoQA, COLLABLLM drops non-ambiguous accuracy from 90.4% to 72.3%, suggesting over-asking of clarification questions. Macro F1 improvement over the base model is only 1.77 points (55.08% vs 53.31%).
- Only one model family and size (Llama-3.1-8B) is evaluated. Scalability and generalization to other architectures and scales is untested.

# Questions

- Why were no existing multiturn training methods (MTPO, ARCHER, or the DPO-based clarification approach of Chen et al. 2024) included as empirical baselines? This is the most significant gap in the evaluation.
- Can you provide an SFT baseline trained on multiturn conversation data generated without MR-guided response selection (e.g., using random or first-sampled responses)? This would isolate whether improvements come from the MR framework or from simply training on multiturn data curated by a strong model (GPT-4o).
- How do you address the concern that ITR gains may be inflated due to the model being trained with an LLM-judged interactivity reward and then evaluated with an LLM-judged interactivity metric? Have you measured correlation between LLM-judged ITR and human-judged interactivity?
- Can you report confidence intervals for the simulated experiments and statistical significance tests (e.g., paired t-tests or bootstrap) for the user study?
- The generalization experiment shows COLLABLLM over-asks clarification questions on non-ambiguous inputs (72.3% vs 90.4%). How would you calibrate this behavior for deployment?
- How sensitive are results to the user simulator quality? Have you quantified performance when using different simulators or measured the sim-to-real gap?
- What is the total training compute overhead of COLLABLLM (including all forward simulation costs) compared to standard DPO/PPO training?

# Limitations

- Dependence on high-quality proprietary user simulators for training. Open-source models reportedly perform poorly as simulators, creating a practical bottleneck for reproducibility and wider adoption.
- Only validated on one model size (8B) and family (Llama). Generalization to other scales and architectures is unknown.
- The forward simulation window is limited to w=2-3 turns, which may not capture longer-horizon planning requirements in extended conversations.
- Heavy reliance on LLM judges for both training and evaluation introduces systematic biases that are difficult to characterize or control for.
- Potential for information extraction: The proactive questioning behavior could theoretically be exploited to elicit sensitive information from users, though safety evaluation suggests this is not a significant concern with aligned base models.

# Scores

- **Originality**: 3
- **Quality**: 2
- **Clarity**: 3
- **Significance**: 2
- **Soundness**: 2
- **Presentation**: 3
- **Contribution**: 2
- **Overall**: 5
- **Confidence**: 4

# Decision: Reject