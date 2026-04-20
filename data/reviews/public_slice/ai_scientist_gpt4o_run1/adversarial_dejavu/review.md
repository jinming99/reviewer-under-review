# Summary

The paper proposes the Adversarial Déjà Vu hypothesis, claiming unseen LLM jailbreaks are recombinations of previous attack patterns. It introduces Adversarial Skill Compositional Training (ASCoT), using a sparse dictionary of adversarial skills to boost robustness against such attacks. Using skill extraction and dictionary learning, the paper suggests unseen attacks can be broken down into recomposed primitive skills, theoretically supporting this claim.
# Strengths

- Novel approach to using adversarial skill recombination.
- Comprehensive analysis of jailbreak trends.
- Innovative concept of Adversarial Skill Compositional Training (ASCoT).

# Weaknesses

- Limited originality in leveraging existing adversarial concepts.
- Insufficient empirical grounding of theory.
- Overly complex implementation with unclear reproducibility.
- Lack of robust longitudinal studies and practical application validation.
- Dense language diminishing clarity and accessibility.

# Questions

- How does the dictionary handle novel primitives that genuinely deviate from historical patterns?
- Is there a detailed breakdown of the computational costs linked to the dictionary learning and skill composition processes?
- How does ASCoT compare with state-of-the-art methods in diverse and non-academic real-world scenarios?

# Limitations

- Does not address computational limits handling extremely large skill compositions.
- Potential ethical misuse in understanding adversarial skills.
- Dependency on specific LLMs like GPT-4.1 raises reproducibility concerns.

# Scores

- **Originality**: 2
- **Quality**: 2
- **Clarity**: 2
- **Significance**: 2
- **Soundness**: 2
- **Presentation**: 2
- **Contribution**: 2
- **Overall**: 3
- **Confidence**: 4

# Decision: Reject