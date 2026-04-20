# Summary

This paper proposes the 'Adversarial Déjà Vu' hypothesis: that novel jailbreak attacks on LLMs are not fundamentally new but are recombinations of adversarial skills from previous attacks. The authors build an automated pipeline using GPT-4.1 to extract adversarial skills from 1,494 prompt pairs spanning 32 jailbreak papers over two years, then compress them via sparse dictionary learning into a compact 'Jailbreak Dictionary' of ~397 primitives. They show that unseen attacks can be explained as sparse compositions of these primitives, with explanatory power increasing monotonically over time. Building on this insight, they introduce ASCoT (Adversarial Skill Compositional Training), which generates training data by composing diverse combinations of skill primitives. ASCoT is evaluated on LLaMA-3.1-8B, Zephyr-7B, and Mistral-7B against both seen and unseen attacks, demonstrating improved robustness with low over-refusal rates. Additional ablations study the effects of skill coverage and compositional depth.
# Strengths

- The Adversarial Déjà Vu hypothesis provides a novel and intuitive conceptual framework for understanding jailbreak evolution. Viewing unseen jailbreaks as recompositions of known skills is a genuinely useful perspective that could inform future defense research.
- The temporal cutoff study design is well-conceived: partitioning 32 attacks into seen/unseen sets across multiple cutoffs and showing monotonically increasing explanatory power provides systematic evidence for the hypothesis.
- ASCoT shows strong empirical results across three model families (LLaMA, Zephyr, Mistral) with competitive robustness against unseen attacks while maintaining favorable over-refusal rates, outperforming baselines including CAT, LAT, WildJailbreak, and attack-specific training.
- The ablation studies on coverage dividend (Section 4.2) and compositional depth (Section 4.3) are insightful, revealing that robustness scales with skill coverage and that different attack complexities require different training depths—these are actionable findings for practitioners.
- Providing both closed-source (GPT-4.1) and open-source (Qwen3) pipeline variants demonstrates transferability and supports reproducibility. The comparable performance of both variants strengthens confidence.
- The random skill subset control (Appendix J) provides evidence that dictionary learning compression contributes meaningfully beyond simply having a diverse set of skills.

# Weaknesses

- Circularity in evaluation: GPT-4.1 performs skill extraction, interprets dictionary atoms, and serves as the primary explainability judge. While Claude 3.7 Sonnet is used as a cross-check, both LLMs may share systematic biases. A human evaluation component, even on a subset, would substantially strengthen the core hypothesis claims.
- The unseen attack evaluation set is small—only 6 post-cutoff attacks—limiting the generalizability of the hypothesis. These attacks originate from the same research community and may naturally share strategies, making the 'déjà vu' finding partly an artifact of community conventions rather than a fundamental property.
- The linear composition assumption in embedding space is strong and insufficiently validated. Reconstruction MSE alone does not confirm that semantic composition behaves linearly; the paper acknowledges this is a 'working modeling choice' but the dictionary learning framework rests on it.
- The hypothesis risks tautology at certain abstraction levels: if skills are sufficiently generic (e.g., 'role-playing,' 'academic framing'), most attacks will trivially appear to recombine them. The paper does not analyze at what granularity the dictionary becomes trivially explanatory vs. genuinely predictive.
- Missing component ablation: ASCoT's 40.5k training examples include adversarial compositions, benign data, over-refusal calibration (XSTest upsampled 15x), and multiple harmful datasets. The relative contribution of each component is not isolated—some gains may come from the data mixture or the aggressive over-refusal calibration rather than the skill composition paradigm.
- The multi-turn generalization claim is supported by only one attack (GALA), which is insufficient for a strong conclusion. A broader multi-turn evaluation would be needed.
- No discussion of adversarial adaptation: if attackers know the defender uses ASCoT, they could target strategies poorly represented in the dictionary. The paper does not address robustness under adaptive threat models.

# Questions

- Can you provide human evaluation of explainability scores, even on a subset, to validate that the LLM-based scoring is not systematically inflated?
- What is the contribution of each training data component (adversarial compositions, benign data, over-refusal calibration, vanilla harmful queries) to ASCoT's performance? An ablation removing each component would clarify the source of gains.
- How sensitive are results to the abstraction level of extracted skills? If you constrain extraction to very fine-grained vs. very coarse skills, how does this affect both explanatory power and downstream robustness?
- The explainability plateau in Figure 3 could reflect LLM evaluation ceiling effects rather than genuine skill saturation. Have you tested whether scores plateau similarly when evaluating truly random/unrelated skills as explanations?
- How would ASCoT perform against attacks deliberately designed to exploit skills NOT in the dictionary—i.e., adaptive adversaries aware of the skill taxonomy?
- What is the total computational cost of the full pipeline from skill extraction through ASCoT training?

# Limitations

- The paper scopes to single-turn, language-based jailbreaks but makes multi-turn generalization claims based on only one evaluation attack (GALA).
- The approach assumes the adversarial skill space is approximately finite and linearly composable—novel attack paradigms violating these assumptions could circumvent ASCoT.
- No discussion of adaptive adversaries who might specifically target gaps in the skill dictionary.
- The reliance on frontier LLMs throughout the pipeline means defense quality is upper-bounded by extraction/composition model capabilities.
- The jailbreak dictionary and skill composition pipeline could potentially be repurposed for attack generation, though the authors' ethics statement addresses this concern reasonably.

# Scores

- **Originality**: 3
- **Quality**: 3
- **Clarity**: 3
- **Significance**: 3
- **Soundness**: 3
- **Presentation**: 3
- **Contribution**: 3
- **Overall**: 6
- **Confidence**: 4

# Decision: Accept