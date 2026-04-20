# Summary

The paper examines the effectiveness of Reinforcement Learning with Verifiable Rewards (RLVR) in enhancing reasoning capabilities of large language models (LLMs). It probes if RLVR training elicits novel reasoning patterns beyond those of the base models. Despite RLVR improving sampling efficiency towards correct paths, it does not fundamentally expand reasoning capabilities. The study reveals that all reasoning paths used by RLVR models are present in the base model, underscoring a significant gap in leveraging RL's potential. The findings suggest that distillation, rather than RLVR, can introduce new reasoning patterns.
# Strengths

- Comprehensive evaluation of RLVR across numerous benchmarks and tasks.
- Thorough comparison between RLVR and base models.
- Insightful discussion on the limitations of current RLVR methods.

# Weaknesses

- Limited exploration of new RLVR paradigms or optimization strategies.
- Lacks actionable solutions to overcome identified limitations.
- Some findings reiterate already known limitations of RL without proposing significant advancements.

# Questions

- What specific strategies could be explored to enhance RLVR effectiveness beyond current capabilities?
- How do the findings of this paper relate to existing literature on RL limitations in LLMs?
- What metrics or criteria should future RLVR developments focus on to genuinely enhance reasoning capabilities?

# Limitations

- The study acknowledges RLVR is bounded within the base model's reasoning capabilities. Potential enhancements via multi-turn interactions, better exploration strategies, and continual scaling are suggested but not explored.
- Societal impacts include the potential propagation of biases inherent in base models as RLVR doesn't introduce new reasoning capabilities.

# Scores

- **Originality**: 2
- **Quality**: 3
- **Clarity**: 3
- **Significance**: 2
- **Soundness**: 3
- **Presentation**: 3
- **Contribution**: 2
- **Overall**: 3
- **Confidence**: 4

# Decision: Reject