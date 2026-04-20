# Overall Feedback

COLLABLLM presents a well-motivated framework for training LLMs to be more collaborative in multiturn interactions, with a clear formulation of Multiturn-aware Rewards and supporting experiments including a large user study. However, the paper has several quantifiable issues: a numerical error in the reported MATH-Chat interactivity improvement that inflates a headline result, a contradictory illustration in Figure 2, an incorrect causal inference derivation in the appendix, and an overclaimed generalization result. The core idea—using forward simulation to estimate long-term reward of individual responses—is sound and the experimental design is thorough, but the technical presentation would benefit from corrections to the specific issues identified below.

# Detailed Comments


## Comment 1: MATH-Chat ITR relative improvement computed against wrong baseline


> Rel. Improv. indicates the relative improvements of CollabLLMs trained with Online DPO over Proactive Base.


The table caption states that Rel. Improv. is computed against Proactive Base. For MediumDocEdit-Chat ITR and BigCodeBench-Chat ITR, this is correct: (92−62)/62 ≈ 48.4% and (52.0−33.7)/33.7 ≈ 54.3%. However, for MATH-Chat ITR, the reported 36.4% equals (60−44)/44 = 36.36%, which is the improvement over Base (ITR=44.0), not Proactive Base (ITR=46.0). The correct value over Proactive Base is (60−46)/46 = 30.4%. This error propagates to the headline claim of '46.3% improved interactivity' in the abstract: averaging the table values gives (48.3+54.3+36.4)/3 = 46.3%, but the corrected average is (48.4+54.3+30.4)/3 ≈ 44.4%. The abstract's flagship number is thus inflated by roughly 2 percentage points due to an inconsistent baseline choice for one cell in Table 1.


*Type: technical*


## Comment 2: Figure 2 labels identical token counts as both 'Low Efficiency' and 'High Efficiency'


> : Low Efficiency (1.39k tokens read) 
: Low Quality (BLEU=0.32)  
 
: Low Interactivity (LLM Judge score=0.2)


In Figure 2, the non-collaborative LLM example is annotated with 'Low Efficiency (1.39k tokens read)' while the COLLABLLM example is annotated with 'High Efficiency (1.39k tokens read)'. Both show exactly 1.39k tokens read. Since the paper defines its efficiency metric in Eq. 4 as a penalty on TokenCount(t), identical token counts should yield identical efficiency assessments. Labeling the same quantity as both 'Low' and 'High' efficiency directly contradicts the paper's own metric. The quality and interactivity labels differ appropriately (BLEU 0.32 vs 0.46, LLM Judge 0.2 vs 0.8), so it appears the token count for one of the examples was not updated when constructing the figure.


*Type: logical*


## Comment 3: Equation 5 is not front-door adjustment and contains a mathematical error


> the causal effect of a model response mj on the final conversation trajectory can be expressed using front-door adjustment (Pearl, 2009; Pearl et al., 2016):
\sum R∗(t1:K | g)P(t1:K | th
j )P(th
j ) =
\sum R∗(t1:K | g)P(t1:K | th
j ) = Et1:K∼P (t1:K|th
j )R∗(t1:K | g).


Three problems with this equation. First, the model response mj does not appear anywhere in the expression—th_j is defined as t_{1:j−1} ∪ {u_j}, which excludes mj. Conditioning on th_j marginalizes over all possible mj, so this computes the expected reward given the history before the model responds, not the causal effect of a specific mj. The causal effect of mj is already correctly expressed in Eq. 1 of the main text. Second, the first equality is incorrect: since the sum is over t_{1:K} and P(th_j) is constant with respect to t_{1:K}, it factors out, giving P(th_j) · Σ R* P(t|th_j) ≠ Σ R* P(t|th_j) unless P(th_j)=1. Third, the front-door adjustment (Pearl 2009, Theorem 3.3.4) has a specific algebraic form involving a mediating variable Z: P(Y|do(X)) = Σ_z P(z|X) Σ_{x'} P(Y|x',z)P(x'). The equation shown is a simple conditional expectation and bears no resemblance to this formula. The claimed connection to causal inference is not substantiated by the derivation.


*Type: technical*


## Comment 4: Overclaimed generalization: 'maintaining high accuracy' despite 20% relative drop on non-ambiguous questions


> proactively asks questions about 50% of the time while maintaining high accuracy on unambiguous inputs.


Table 2 shows that COLLABLLM achieves 72.32% accuracy on non-ambiguous questions, compared to 90.40% for the Llama-3.1-8B base model—a drop of 18 percentage points (20% relative). Describing 72.32% as 'maintaining high accuracy' is misleading when the base model achieves 90.40% on the same split. The improvement on ambiguous questions (16.26% → 52.84%) is genuine and substantial, and the macro accuracy does improve. However, the framing obscures a meaningful degradation: COLLABLLM unnecessarily asks clarifying questions for roughly 28% of unambiguous inputs. A more balanced presentation would acknowledge this tradeoff explicitly rather than characterizing both sides as positive.


*Type: logical*


## Comment 5: Appendix A.2 distinction from trajectory-level methods is overstated


> this approach is fundamentally observational—it captures statistical associations between responses and final outcomes, without disentangling how individual responses causally influence future turns.


The paper positions its approach against methods like MTPO (Shani et al., 2024) by claiming they are 'fundamentally observational' while COLLABLLM is 'interventional' because it uses forward simulation. However, the forward simulation in COLLABLLM samples from P(t_{j+1:K} | t_{1:j})—a conditional distribution from the same generative process (user simulator + policy model). This is still a Monte Carlo estimate of a conditional expectation, not a true intervention in the do-calculus sense, because there is no confounding to adjust for: the model directly generates mj and the simulator directly generates future user turns. In both COLLABLLM and trajectory-level methods, the model controls the responses and the reward is observed—the difference is in granularity of credit assignment (per-turn vs per-trajectory), not in the observational-vs-interventional distinction. Framing the advantage as causal vs. observational overstates the theoretical contribution when the practical advantage is really about finer-grained reward attribution.


*Type: logical*


## Comment 6: Intrinsic reward token penalty saturates for typical MATH-Chat conversations


> Rint(t) = −min[λ · TokenCount(t), 1] + RLLM(t)


With λ = 5×10⁻⁴ (Table 6) and typical MATH-Chat conversations averaging ~2.4k–3.4k tokens (Table 1), the token penalty λ·TokenCount ≈ 1.2–1.7 exceeds the clamp at 1 for most conversations. This means the efficiency term in R_int is saturated at −1 for the majority of training examples, providing zero gradient signal with respect to token count differences. The model cannot distinguish between a 2.5k-token conversation and a 3.5k-token one through this reward component, as both are clamped. While the clamp is described as maintaining 'balance with other metrics,' the practical consequence is that efficiency incentives vanish for all but the shortest MATH conversations, potentially explaining why the efficiency gains for MATH-Chat (18.3%) are driven primarily by the extrinsic reward favoring more direct strategies rather than the token penalty itself.


*Type: technical*
