# Overall Feedback

This paper presents a thought-provoking empirical investigation into whether RLVR genuinely expands LLM reasoning capabilities beyond what the base model already possesses. The experimental breadth—covering multiple model families, RL algorithms, and task domains—is commendable, and the core finding that pass@k curves cross over is well-demonstrated. However, several issues weaken the analysis: the proposed Sampling Efficiency Gap metric has an ambiguous definition and numerical values that are inconsistent with the paper's own tables, the perplexity analysis underpinning a central claim rests on only two problems, and the paper's strongest claims about 'reasoning patterns' overreach the evidence, which primarily concerns problem solvability rather than the nature of reasoning itself.

# Detailed Comments


## Comment 1: Ambiguous direction of subtraction in the Sampling Efficiency Gap definition


> we propose the Sampling Efficiency Gap (∆SE), defined as the difference between the RL-trained model's pass@1 and the base model's pass@k (we use k = 256 in our evaluation). Lower ∆SE is better.


In standard English, 'the difference between A and B' most naturally reads as A − B, which here would be RL_pass@1 − base_pass@256. Since the RL model's pass@1 is consistently lower than the base model's pass@256 (the whole point of the paper), this would yield a negative value. Yet the reported ∆SE values are all positive (e.g., 0.359, 0.410, 0.206 in Figure 8), and the paper says 'lower ∆SE is better'—which only makes sense if ∆SE = base_pass@256 − RL_pass@1. The definition as written contradicts the sign of the reported values. This should be stated unambiguously, e.g., as ∆SE = pass@k_base − pass@1_RL.


*Type: logical*


## Comment 2: Reported ∆SE values and algorithm attribution are inconsistent with Table 3


> Different RL algorithms yield slightly different ∆SE values (i.e., ranging from GRPO's 43.9 to RLOO's best 42.6 on the in-domain test set). Furthermore, we observe that ∆SE remains consistently above 40 points across different algorithms


Computing ∆SE = base_pass@256 − RL_pass@1 from Table 3 for the in-domain test set (Omni-MATH-Test, base pass@256 = 69.1): GRPO = 69.1−25.1 = 44.0 (text says 43.9, minor rounding); RLOO = 69.1−28.1 = 41.0 (text says 42.6, a discrepancy of 1.6 points). The value 42.6 actually matches DAPO (69.1−26.5 = 42.6), not RLOO. Moreover, the claimed range of 42.6–43.9 omits ReMax at 45.3 and the actual best RLOO at 41.0, understating the true variation across algorithms (41.0–45.3, a span of 4.3 points vs. the claimed 1.3 points). This misattribution and narrowed range make the algorithms appear more similar than the data actually show.


*Type: technical*


## Comment 3: Perplexity analysis supporting a central claim is based on only two problems


> We randomly sample two problems from AIME24 and employ Qwen2.5-7B-Base and SimpleRL-Qwen2.5-7B-Base to generate 16 responses for each problem


The claim that 'the reasoning paths produced by RLVR models already exist within the output distribution of the base model' is one of the paper's strongest and most cited conclusions. Yet the perplexity analysis in Figure 6 is based on just 2 randomly selected AIME24 problems with 16 responses each. This is an extremely small sample from which to draw a general conclusion about the relationship between base and RLVR model distributions. AIME24 problems vary widely in difficulty and reasoning structure, and two problems cannot represent this diversity. While the solvable-problem coverage analysis (Table 2) provides complementary evidence, the perplexity analysis is the only evidence that speaks to the distributional claim about reasoning paths, and its scope is insufficient for the generality of the conclusion.


*Type: technical*


## Comment 4: Claims about 'reasoning patterns' overshoot what solvability evidence supports


> current training does not elicit fundamentally new reasoning patterns. We observe that while RLVR-trained models outperform their base models at smaller values of k (e.g., k=1), base models achieve higher pass@k score when k is large.


The paper's primary evidence is that the set of problems solvable by RLVR models is approximately a subset of those solvable by the base model at large k. This is a claim about problem solvability. But the paper repeatedly extends this to 'fundamentally new reasoning patterns'—a stronger claim about the nature of the model's reasoning strategies. It is logically possible for RLVR to introduce new reasoning approaches (e.g., novel proof strategies, different problem decompositions) that happen to apply only to problems already solvable by the base model through other approaches. The pass@k evidence cannot distinguish between 'RLVR finds the same reasoning paths more efficiently' and 'RLVR finds different paths to the same problems.' The perplexity analysis begins to address this distinction but, as noted, covers only two problems. The conflation weakens the paper's strongest conclusions.


*Type: logical*


## Comment 5: Showcased 'correct' base model CoT contains two canceling arithmetic errors


> 900 = 1924 − 437 − 2 × 234 − 3 × X
900 = 1924 − 805 − 3 × X
900 = 1119 − 3 × X


Figure 20 is presented as a correct CoT from Qwen2.5-7B-Base for AIME24 Question 16, described as 'manually selected from 2048 samplings for the hardest questions in AIME24.' However, the arithmetic contains two errors: the sum 195+367+562+900 = 2024, not 1924 (off by 100), and the penalty 437+2×234 = 905, not 805 (also off by 100). These errors cancel because 2024−905 = 1924−805 = 1119, so the final answer X=73 happens to be correct. This raises concern about the rigor of the manual CoT inspection process described in Section 3.1, where the authors report that 24/25 (GSM8K) and 5/6 (AIME24) hard problems had 'correct' CoTs. If CoTs with coincidentally canceling arithmetic errors are counted as correct, the reported validity rates may be overstated.


*Type: technical*


## Comment 6: Distillation comparison lacks a controlled baseline


> distillation can transfer new reasoning patterns from a stronger teacher to the student. As a result, distilled models often demonstrate an expanded reasoning scope beyond that of the base model.


The paper contrasts RLVR (bounded by the base model) with distillation (which expands beyond it), using DeepSeek-R1-Distill-Qwen-7B as the exemplar. However, this comparison is not controlled for the information provided during training. The distilled model is fine-tuned on long CoT traces from DeepSeek-R1, a vastly more capable model. That supervised fine-tuning on high-quality data from a stronger source expands the student's capabilities is expected and well-established. The more informative comparison would hold the training data source constant—e.g., comparing RLVR on problems where the teacher's CoT traces are available versus distillation on those same traces—to isolate the effect of the learning paradigm from the effect of injecting external knowledge. Without this control, the conclusion that 'distillation is fundamentally different from RLVR' is confounded by the additional information the distilled model receives.


*Type: logical*
