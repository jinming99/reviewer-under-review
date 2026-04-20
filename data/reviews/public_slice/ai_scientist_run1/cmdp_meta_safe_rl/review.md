# Summary

This paper studies meta-safe reinforcement learning (Meta-SRL) through a CMDP-within-online framework. The meta-learner sequentially updates policy initializations and learning rates for a within-task safe RL algorithm (CRPO) by performing online gradient descent on upper bounds of the optimality gap and constraint violations. These upper bounds are estimated using suboptimal policies and stationary distribution corrections (DualDICE) from collected trajectories. The paper provides task-averaged regret bounds (TAOG and TACV) that improve with task-similarity (static setting) or task-relatedness (dynamic setting). Technical contributions include an analysis of the CMDP optimization landscape using tame geometry, inexact online gradient descent regret bounds, and adaptive learning rate schemes. Experiments on Frozen Lake, Acrobot, Half-Cheetah, and Humanoid environments demonstrate improved performance over naive baselines.
# Strengths

- Addresses an important and understudied problem: provable guarantees for meta-learning in constrained MDPs. This appears to be the first work providing such guarantees.
- The use of tame geometry and the Kurdyka-Łojasiewicz inequality to bound the distance between suboptimal and optimal policies in an algorithm-agnostic manner (Theorem 3.1) is a creative and novel technical contribution that may be of independent interest.
- The framework handles practical challenges: it does not require access to globally optimal policies, uses off-policy estimation (DualDICE) for stationary distribution corrections, and supports adaptive learning rates that do not require knowledge of horizon-dependent quantities.
- Comprehensive theoretical development with clear progression from idealized (Lemma 1) to practical settings (Theorem 3.2, Corollary 1), covering both static and dynamic regret with explicit dependence on task-similarity/relatedness.
- The decomposition of estimation error into three sources (distribution mismatch, DualDICE error, policy suboptimality) in Equation 4 provides a modular framework that could accommodate alternative estimation methods.

# Weaknesses

- Significant theory-practice gap: All theoretical results assume tabular CMDPs with softmax parametrization, yet experiments include continuous control tasks (Half-Cheetah with 17D state, Humanoid with 376D observations). No discussion bridges this gap.
- The bound in Theorem 3.1 involves a function h from the KL inequality that is only characterized qualitatively ('strictly increasing continuous with h(0)=0'). Without knowing its growth rate, the bound could be vacuous. Practical tightness is never assessed.
- Experimental baselines are uniformly naive: random initialization, simple averaging, pre-trained from one task, and Follow-the-Average-Leader. No comparison with any meta-RL method (MAML, ProMP) or modern safe RL approach adapted to the multi-task setting.
- The core theoretical prediction—that TAOG and TACV scale with task-similarity D* or task-relatedness V_ψ—is never quantitatively validated in experiments. No ablation varies similarity in a controlled way while measuring these quantities.
- The framework is restricted to CRPO as the within-task algorithm. While extensions are mentioned, no concrete analysis is provided for other safe RL algorithms, limiting practical generality.
- Very limited training steps in experiments (5-10 steps on test tasks), which makes it difficult to assess convergence properties or to distinguish the meta-learning benefit from simply running more within-task iterations.
- The paper is very dense (49 pages total) with heavy notation. Many important details, including proofs and algorithm specifics, are deferred to appendices, making the main text hard to follow independently.

# Questions

- Can you provide explicit characterizations of the function h in Theorem 3.1 for specific problem instances (e.g., tabular CMDPs with linear rewards)? What is its typical growth rate?
- How do the theoretical guarantees extend to the continuous state-action settings used in Half-Cheetah and Humanoid experiments? If they do not directly extend, what is the justification for using these environments?
- Can you quantitatively measure the empirical task-similarity D* and task-relatedness V_ψ in your experiments and demonstrate how TAOG/TACV correlate with these quantities?
- Why were no existing meta-RL methods (e.g., MAML with constraint handling) used as baselines? This would provide much more informative comparisons.
- Assumption 4 was introduced to address a gap in the original CRPO proof. Can you elaborate on what was incorrect in the original derivation and whether your fix affects the single-task CRPO guarantees?
- What is the computational overhead of running DualDICE after each task, and how does this scale with state-action space size?

# Limitations

- The framework is limited to CRPO as the within-task algorithm, restricting applicability to other safe RL methods.
- Theoretical results hold only for tabular settings with softmax parametrization; extension to function approximation is not provided.
- The bounds depend on opaque quantities (function h, cumulative inexactness E_T) whose practical magnitudes are unclear.
- The method permits constraint violations during learning, which may be unacceptable in safety-critical applications.
- No discussion of computational overhead of DualDICE estimation after each task.
- Potential negative societal impact discussion is limited to brief remarks about fairness applications.

# Scores

- **Originality**: 3
- **Quality**: 2
- **Clarity**: 2
- **Significance**: 2
- **Soundness**: 2
- **Presentation**: 2
- **Contribution**: 2
- **Overall**: 4
- **Confidence**: 4

# Decision: Reject