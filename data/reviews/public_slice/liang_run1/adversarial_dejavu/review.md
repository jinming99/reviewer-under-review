Review outline:

**1. Significance and novelty**

- The paper introduces a compelling conceptual reframing: rather than treating each new jailbreak as fundamentally novel, it posits that jailbreaks are sparse recombinations of a finite set of adversarial skill primitives ("Adversarial Déjà Vu" hypothesis). This is an intellectually appealing and potentially impactful perspective for the AI safety community.
- The technical pipeline—LLM-based skill extraction → embedding → sparse dictionary learning → LLM-augmented basis pursuit for interpretation—is a creative fusion of classical signal processing tools (K-SVD, BPDN) with modern LLM capabilities. The resulting "Jailbreak Dictionary" is a novel artifact.
- ASCoT offers a data-centric alternative to adversarial training that is simple, modular, and apparently effective. The idea of training on compositional skill combinations rather than specific attacks is intuitive and actionable.
- The temporal cutoff study design (partitioning 32 attacks over 2 years into seen/unseen sets across multiple cutoffs) is a principled evaluation methodology that is underused in the jailbreak defense literature.

**2. Potential reasons for acceptance**

- **Strong empirical results across models and attacks:** ASCoT consistently achieves the lowest mean harmfulness scores on unseen attacks across LLaMA-3.1-8B, Zephyr-7B, and Mistral-7B, while maintaining competitive over-refusal rates (Table 2). It even favorably compares against frontier reasoning models (o4-mini, Claude Sonnet-4-Thinking) at a fraction of the scale (Table 3).
- **Well-structured hypothesis-driven narrative:** The paper flows logically from hypothesis formulation → empirical validation of the hypothesis (Section 2) → a defense method motivated by the hypothesis (Section 3) → ablation studies dissecting why it works (Section 4: coverage dividend, compositional depth). This makes the contribution legible and scientifically grounded.
- **Thorough ablations and controls:** The coverage dividend experiment (Section 4.2), compositional depth analysis (Section 4.3), novel composition generalization test (Section 4.4/Table 4), and random skill subset control (Appendix J) collectively provide strong evidence that the gains come from structured skill coverage, not data volume or arbitrary diversity.
- **Reproducibility and openness:** The paper reproduces the full pipeline with an open-weight model (Qwen3-235B), uses a second judge (Claude 3.7 Sonnet) for cross-model validation of explainability scores, and provides extensive appendix detail (extraction prompts, composition prompts, training details, full attack lists).

**3. Potential reasons for rejection**

- **The "Adversarial Déjà Vu" hypothesis is validated via a circular, LLM-as-judge pipeline with limited ground truth.**
  - Explainability scores (Table 1, Figure 3) are produced by GPT-4.1 and Claude 3.7 Sonnet judging whether LLM-extracted skills from unseen attacks can be explained by LLM-extracted and LLM-named dictionary primitives. Every stage is mediated by the same class of models, creating a risk of systematic bias—LLMs may find LLM-generated explanations plausible regardless of true semantic overlap.
  - Using a second LLM judge (Claude) mitigates single-model bias but does not address the deeper issue: there is no human evaluation of explainability, no ground-truth annotation of what skills an attack "truly" uses, and no adversarial probing of the pipeline (e.g., testing on a synthetic attack designed to be genuinely novel). The 4.2–4.3 explainability scores are difficult to interpret without a calibration baseline showing what score a truly novel, unexplainable skill would receive.

- **The linearity assumption in embedding space is strong and insufficiently interrogated.**
  - The entire dictionary learning framework rests on the assumption that adversarial skills compose approximately linearly in the embedding space of text-embedding-3-large. The paper acknowledges this (footnote 1, Section 2.3) but provides no direct validation—e.g., no analysis of whether the embedding space actually exhibits meaningful linear structure for semantic skill composition, no comparison with nonlinear alternatives (e.g., kernel methods, neural decomposition).
  - Reconstruction MSE is reported only in the hyperparameter sweep (Appendix M) for seen data. The unseen reconstruction fidelity is proxied entirely through the LLM-judged explainability score, which conflates embedding-space reconstruction quality with the LLM's post-hoc rationalization ability. A direct quantitative analysis (e.g., cosine similarity of reconstructed vs. true unseen skill embeddings) would be more convincing.

- **Evaluation scope is narrow and potentially favorable to ASCoT by design.**
  - Only 6 unseen attacks are evaluated, all of which are language-based single-turn attacks (with the exception of GALA). The paper's own Table 2 shows ASCoT's advantage on GALA (multi-turn) is modest for some models (e.g., Zephyr ASCoT open: 0.09 vs. WildJailbreak: 0.46, but Mistral ASCoT closed: 0.07 vs. LAT: 0.68—strong, yet LAT*: 0.71 also fails). The generalization claim to multi-turn is based on a single attack.
  - The composition pipeline uses DeepSeek-V3-Chat to generate training data by rewriting queries with selected skill primitives. Since the unseen attacks are also generated by LLMs (e.g., AutoDAN-Turbo, PAIR), there is a potential distribution overlap: ASCoT may succeed partly because LLM-generated adversarial compositions share stylistic patterns with LLM-generated attacks, rather than because of true skill-level generalization. No analysis disentangles this confound.

- **The practical threat model and adaptive attacker analysis are underdeveloped.**
  - The paper does not evaluate against adaptive adversaries who are aware of ASCoT's defense mechanism. An attacker who knows the defender trains on skill compositions could deliberately craft attacks that exploit skills outside the dictionary's coverage or use non-compositional strategies (e.g., entirely novel encoding schemes, multi-modal inputs). The claimed "coverage dividend" may not hold against adversaries specifically targeting coverage gaps.
  - The paper explicitly scopes out fine-tuning attacks and non-language attacks but does not discuss other in-scope threats like very long multi-turn escalation, model-specific prompt injection, or attacks exploiting the specific refusal templates used in training (Appendix C lists only 20 fixed refusal strings, which could be reverse-engineered by an attacker to probe boundaries).

**4. Suggestions for improvement**

- **Add human evaluation of explainability and dictionary quality.** Even a small-scale human study (e.g., 50–100 unseen skills rated by domain experts) would substantially strengthen the core hypothesis. Include calibration examples—synthetic "novel" skills designed to be outside the dictionary—to establish a meaningful lower bound on the explainability scale and demonstrate the score is discriminative.

- **Directly evaluate embedding-space reconstruction quality for unseen skills.** Report quantitative metrics (cosine similarity, MSE) of the sparse reconstruction of unseen skill embeddings, not just LLM-judged explainability. Compare dictionary learning against simpler baselines (e.g., k-means clustering, PCA) and nonlinear alternatives to justify the modeling choice.

- **Expand the unseen attack evaluation set and include adaptive attacks.** Test on a broader set of held-out attacks (ideally including truly novel categories not yet published), and design at least one adaptive attack scenario where the adversary has knowledge of the defense (e.g., specifically targeting uncovered skill regions or exploiting the fixed refusal template set). This would make the robustness claims far more credible for a top-tier venue.

- **Disentangle skill-level generalization from LLM stylistic overlap.** Conduct an ablation where ASCoT training data is generated by a non-LLM process (e.g., rule-based or template-based skill composition) to test whether the gains persist without shared LLM generation artifacts. Alternatively, evaluate on human-crafted jailbreaks (e.g., in-the-wild forum jailbreaks not generated by LLMs) to test whether the compositional skill hypothesis holds beyond LLM-generated attacks.