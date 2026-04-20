# Overall Feedback

This paper introduces a novel and theoretically interesting CMDP-within-online framework for meta-safe reinforcement learning, extending the ARUBA-style meta-learning approach to constrained MDPs. The key ideas—using stationary distribution corrections for inexact online learning, leveraging tame geometry for estimation error bounds, and adapting learning rates—are creative and well-motivated. However, the paper contains several technical errors that undermine confidence in the stated results. Most critically, there is a factor-of-M discrepancy between the per-task regret bound from the within-task analysis (Lemma 21/Equation 2) and the loss function used by the meta-algorithm (Equation 5/Algorithm 1), which propagates to Theorem 3.3 and Corollary 1. Additionally, Lemma 4 item 3 bounds the constraint quantity in the wrong direction, the abstract states a rate that does not match Theorem 3.2, and the proof of Corollary 3 uses an incorrect asymptotic approximation. While the underlying framework and proof strategy appear sound and the errors seem correctable, they require careful revision before the theoretical claims can be fully trusted.

# Detailed Comments


## Comment 1: Equation (5) is M times the actual per-task regret, causing an error in Theorem 3.3


> Ut(πt,0, αt) := ct
1
αt
Es∼ν∗
t [DKL(π∗
t |πt,0)] + αt(ct
2M + ct
4
√
M) + ct
3
√
M


I initially assumed Equation (5) defines the per-task regret bound used in the ARUBA-style decomposition. However, comparing with Equation (2) and Lemma 21 (Equation 45), the per-task optimality gap is bounded by (c₁ᵗ)/(α_t M) · E[D_KL] + c₂ᵗ α_t + lower-order terms, where the first term has M in the denominator. Equation (5) instead has c₁ᵗ/α_t (no M) and α_t(c₂ᵗ M + c₄ᵗ√M) in the second term (extra factor of M). This means U_t in Equation (5) is approximately M times the actual per-task suboptimality bound. Since Theorem 3.3 claims R̄_i ≤ L(κ*)/T, but the actual TAOG satisfies R̄_i = (1/T)∑U_{t,0} ≈ (1/T)∑U_t/M = L(κ*)/(MT), the theorem is off by a factor of M. The same discrepancy appears in Algorithm 1's f̂ᵗ_sim definition. This error propagates to Corollary 1: with the correct factor, the dominant rate from the κ-optimization would be O(1/(√M · √T)) rather than the claimed O(1/(M^{3/4}√T)).


*Type: technical*


## Comment 2: Lemma 4 item 3 bounds the constraint cost in the wrong direction


> 3. Jt,i (π∗
t ) −Jt,i (ˆπt) ≤ηt, for i = 1, . . . , p.


Item 3 states J_{t,i}(π*_t) − J_{t,i}(π̂_t) ≤ η_t, which implies J_{t,i}(π̂_t) ≥ J_{t,i}(π*_t) − η_t. This is a lower bound on the learned policy's cost, but what is needed for the constraint violation bound R_i = E[J_{t,i}(π̂_t)] − d_{t,i} (Equation 2) is an upper bound. The proof says 'item 3 holds obviously since π̂_t is sampled from N_{t,0}', but this argument actually supports J_{t,i}(π̂_t) ≤ d_{t,i} + η_t (because at steps m ∈ N_{t,0}, CRPO ensures approximate constraint satisfaction), which gives the constraint violation bound J_{t,i}(π̂_t) − d_{t,i} ≤ η_t. The correct statement should be E[J_{t,i}(π̂_t)] − d_{t,i} ≤ η_t, matching Equation (2)'s definition of R_i.


*Type: technical*


## Comment 3: Abstract rate does not match Theorem 3.2


> task-averaged regret of O

1
√
M
q
ET
√
T + ˆD∗2


The abstract claims the task-averaged regret is O((1/√M)√(E_T/√T + D̂*²)). However, Theorem 3.2 states R̄_i ≤ O((1/√M)√(1/√T + E_T/T + D̂*²)). The expressions inside the square root differ in two ways: (1) the abstract has E_T/√T while the theorem has E_T/T (different power of T in the denominator), and (2) the theorem contains an additional 1/√T term independent of E_T. These cannot be reconciled: E_T/√T > E_T/T for T > 1, so the abstract's term is strictly larger for the E_T component, while the 1/√T term in the theorem is absent from the abstract. The detailed proof (Theorem E.2) confirms the structure of Theorem 3.2, so the abstract misrepresents the formal result.


*Type: logical*


## Comment 4: Incorrect approximation in the proof of Corollary 3


> using the approximation
q
1
M+
√
M
≊
1
M 1/4


The proof approximates √(1/(M + √M)) ≈ 1/M^{1/4}. For large M, M + √M ≈ M, so √(1/(M + √M)) ≈ 1/√M, which differs from 1/M^{1/4} by a factor of M^{1/4}. Concretely, at M = 10000: √(1/10100) ≈ 0.01, while 1/10000^{0.25} ≈ 0.1—a 10× discrepancy. While 1/M^{1/4} is a valid upper bound on √(1/(M+√M)) for M ≥ 1, calling it an 'approximation' obscures that it is M^{1/4} times looser than the actual value. This looseness is what produces the M^{3/4} rate in Corollary 1; using the correct asymptotic would yield a different (tighter) dependence on M. Together with the factor-of-M issue from Equation (5), this affects whether the claimed improvement from 1/√M (Theorem 3.2) to 1/M^{3/4} (Corollary 1) is valid.


*Type: technical*


## Comment 5: Remark 2 drops path-length terms without justification


> the bounds diminish at a rate O

1
M 3/4√
T

ET +
q
ET
T + ˆV 2
ψ


Corollary 1 (Equation 8) contains the term min(S_T + E_T, P_T + Ẽ_T) inside the square root, where S_T and P_T are the squared path-length and path-length of the comparator sequence. Remark 2 replaces this with just E_T, effectively dropping S_T and P_T. These quantities capture how much the optimal comparator changes across tasks and can be significant in dynamic environments—precisely the setting Corollary 1 addresses. The remark states this simplified rate as the general bound without noting any conditions under which S_T and P_T are negligible. Since the remark is comparing the adaptive rate to Theorem 3.2's rate to demonstrate improvement, this omission could mislead readers about the actual conditions under which the improvement holds.


*Type: logical*


## Comment 6: Cost function arity inconsistency in value function definition


> V i
t,π(s) =
Et [P∞
m=0 γmct,i (sm, am, sm+1) | s0 = s, π]


The cost functions are defined as c_{t,i} : S × A → [0,1], taking two arguments (state, action). However, the value function definition uses c_{t,i}(s_m, a_m, s_{m+1}) with three arguments including the next state s_{m+1}. In the standard CMDP literature, cost functions depend on (s, a) only, consistent with the domain declaration S × A. The value function should use c_{t,i}(s_m, a_m), or the domain should be S × A × S if the next-state dependence is intended. This inconsistency also appears in the action-value function definition with Q^i_{t,π}(s,a).


*Type: technical*


## Comment 7: Humanoid low-similarity setting uses the same range as high-similarity


> To generate tasks with low similarity for the humanoid, the goal direction for each training task is uniformly sampled from a range of [−π/4, π/4].


In Section H.4, the high task-similarity setting samples the humanoid's goal direction from [−π/4, π/4]. The low task-similarity setting states the exact same range [−π/4, π/4]. This appears to be a copy-paste error; by analogy with the half-cheetah experiments (where high similarity uses [0.35, 0.65] and low similarity uses [0.0, 1.0]), the low-similarity humanoid setting should presumably use a wider range such as [−π/2, π/2]. Despite this, the experimental results in Figures 8 and 9 do show different performance patterns, suggesting the actual experiments may have used different ranges than what is stated in the text.


*Type: logical*


## Comment 8: Proof of Corollary 3 has a missing square in the derivative


> dL
dκ = −U init
T
({ψ}t∈[T ])
κ2
−ET
κ2 −T ˆVψ
κ2
+ ct
2M + ct
4
√
M.


In the proof of Corollary 3, the derivative dL/dκ contains the term −TV̂_ψ/κ² where V̂_ψ should be V̂²_ψ (squared). This is because the relevant term in L(κ) is TV̂²_ψ/κ, whose derivative with respect to κ is −TV̂²_ψ/κ². The subsequent formula for κ* = √((U^init_T + E_T + TV̂²_ψ)/(c²_t M + c⁴_t √M)) correctly uses V̂²_ψ, indicating the derivative expression is a typo rather than a propagating error, but it could confuse readers verifying the derivation.


*Type: technical*
