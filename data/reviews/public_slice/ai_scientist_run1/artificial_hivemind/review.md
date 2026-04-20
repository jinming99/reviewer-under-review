# Summary

The paper introduces INFINITY-CHAT, a large-scale dataset of 26K real-world open-ended user queries mined from WildChat, along with a comprehensive taxonomy of open-ended LM queries (6 top-level, 17 subcategories). Using a 100-query subset, the authors study intra-model repetition and inter-model homogeneity across 70+ LMs, revealing what they term the 'Artificial Hivemind' effect — models converge on strikingly similar outputs both within and across model families. The paper also collects 31,250 human annotations (25 per example) for absolute and pairwise preference ratings, showing that LMs, reward models, and LM judges are less calibrated to human ratings on responses that elicit divergent annotator preferences.
# Strengths

- Addresses an important and timely problem: the homogenization of LM outputs in open-ended settings, with implications for creativity and pluralistic alignment.
- Impressive scale: 70+ models evaluated, 26K queries mined, 31K+ human annotations with 25 independent annotators per item, enabling distributional preference analysis that is rare in the literature.
- The inter-model homogeneity analysis is novel — prior work focused on intra-model repetition or narrow synthetic tasks. This paper provides the first systematic cross-model convergence analysis on real-world open-ended queries.
- The taxonomy of open-ended query types is well-constructed and grounded in naturally occurring user-chatbot interactions, identifying underexplored categories such as speculative/hypothetical scenarios and skill development.
- Compelling qualitative examples (e.g., Figure 1 showing 25 models collapsing into two metaphor clusters) make the central phenomenon vivid and intuitive.
- Thorough appendix with extensive model-level breakdowns, annotation interface screenshots, annotator demographics, and paraphrase robustness experiments.

# Weaknesses

- The entire diversity measurement framework relies on cosine similarity from a single embedding model (OpenAI's text-embedding-3-small). This choice is never validated against human judgments of creative diversity. Two responses sharing topical content (e.g., both about time) will have high embedding similarity even if creatively distinct. No alternative metrics (n-gram diversity, BERTScore, topic-model diversity, human-judged diversity) are explored to triangulate findings.
- No human diversity baseline is provided. The paper never measures pairwise embedding similarity among diverse human-authored responses to the same prompts. Without this reference point, the claim that LMs are 'too homogeneous' is ungrounded — we cannot distinguish model-specific convergence from task-inherent constraints.
- The core experimental analyses use only 100 queries (intra/inter-model study) and 50 queries (human annotation study) from a pool of 26K. This small evaluation scope significantly limits generalizability and is not adequately justified.
- Section 4 findings are partly expected by construction: model ratings naturally correlate less with human judgments when human ratings have less variance (similar quality) or more noise (high disagreement). The paper does not control for restricted-range effects or test whether the correlation drop exceeds what would be expected from reduced signal-to-noise ratio alone.
- No causal analysis of why homogeneity occurs. The paper cannot distinguish shared training data, RLHF alignment, memorization, task constraints, or embedding-level artifacts. This limits actionable insights for mitigation.
- The quality-diversity tradeoff is not studied. Diversity is measured at a single decoding configuration without assessing whether more diverse outputs maintain acceptable quality.
- The framing ('Artificial Hivemind,' 'long-term AI safety risks,' 'homogenization of human thought') is stronger than the evidence supports. The paper measures output similarity; it provides no evidence of actual downstream impact on human creativity or behavior.

# Questions

- What is the pairwise embedding similarity among diverse human responses to the same open-ended queries? Without this baseline, how can we assess whether the observed LM similarity levels are abnormally high vs. inherent to the task?
- Have you validated the text-embedding-3-small similarity metric against human judgments of creative diversity? What happens with alternative metrics such as self-BLEU, distinct n-grams, or BERTScore?
- Why were only 100/50 queries used for the main analyses given 26K were available? Have you verified that results are stable across different random subsets?
- For the inter-model similarity analysis, what is the expected similarity for well-formed English text about the same topic? How much of the observed similarity is attributable to topical constraints vs. genuine creative convergence?
- In Section 4, have you considered that the drop in correlation for similar-quality or high-disagreement subsets may partly reflect restricted-range effects? How do you control for this statistical artifact?
- Do results vary meaningfully across taxonomy categories? Do creative tasks show more homogeneity than information-seeking tasks?

# Limitations

- The authors acknowledge English-only scope, lack of causal analysis, and limitations of embedding-based diversity measurement. However, the absence of a human diversity baseline is not adequately flagged as a fundamental limitation.
- The quality-diversity tradeoff is acknowledged but not studied, which is critical for practical implications of the findings.
- Claims about societal impact (homogenization of human thought, AI safety risks) are speculative and not supported by evidence in this paper.
- The small evaluation subsets (100 and 50 queries) for core analyses are insufficiently discussed as a limitation relative to the 26K queries available.
- No significant negative societal impact concerns beyond those discussed by the authors.

# Scores

- **Originality**: 3
- **Quality**: 2
- **Clarity**: 3
- **Significance**: 2
- **Soundness**: 2
- **Presentation**: 3
- **Contribution**: 2
- **Overall**: 4
- **Confidence**: 4

# Decision: Reject