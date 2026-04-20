# Gate Definitions (G0–G7)

These are the fatal-flaw gates used for verdict inference. Gates G1, G2, G4, G5 are **fundamental** — 2+ major/fatal concerns in these categories trigger automatic REJECT.

---

## G0. Central Claims Are Explicit and Falsifiable

**Triggers when**: Paper does not state 1–3 central claims in a way that could be proven wrong. Abstract/introduction lacks specific, falsifiable contribution list.

**Example concerns that map here**: "Claims are vague," "no measurable statement," "contributions not clearly delineated."

---

## G1. Claim–Evidence Mismatch [FUNDAMENTAL]

**Triggers when**: A central claim lacks direct supporting evidence, or the evidence tests something different from what the claim states.

**Example concerns that map here**: "Claims OOD robustness but only tests in-distribution," "claims efficiency but doesn't measure wall-clock time," "main claim not supported by the experiments," "evaluation doesn't test the central hypothesis," "overclaiming — results don't support the breadth of claims."

**Note**: Overclaiming often maps to G1 (evidence doesn't support the scope of the claim) and/or G7 (claims exceed evidence in certainty/scope).

---

## G2. Baseline Fairness [FUNDAMENTAL]

**Triggers when**: Headline improvement depends on weak, missing, or unfair baselines. Baselines don't include strongest competitors, tuning budgets aren't matched, compute/data/backbone not controlled.

**Example concerns that map here**: "Missing comparison to [strong method]," "baselines use default hyperparameters while proposed method is tuned," "unfair comparison — different backbone/training data," "cherry-picks which baseline per dataset."

---

## G3. Method Not Implementable

**Triggers when**: A competent reader cannot re-implement the method. Missing algorithm specification, critical training/eval details, dataset splits, hyperparameters.

**Example concerns that map here**: "Reproducibility concerns," "missing implementation details," "code not available," "key hyperparameters omitted."

---

## G4. Validity Bugs / Leakage / Confounding [FUNDAMENTAL]

**Triggers when**: Obvious threat that could plausibly invalidate the main result and is not addressed. Test leakage, confounding variables, evaluation shortcuts, metric doesn't measure what's claimed.

**Example concerns that map here**: "Data leakage between train and test," "confounding variable not controlled," "evaluation metric doesn't capture the claimed property," "benchmark contamination," "circular evaluation," "the task can be solved by shortcut without the claimed ability."

---

## G5. Novelty Is Trivially Incremental [FUNDAMENTAL]

**Triggers when**: Contribution is essentially "add component X, tune, +1-2% on benchmark" without delivering a transferable insight, new capability, reusable technique, or informative empirical phenomenon.

**Example concerns that map here**: "Limited novelty," "incremental over [prior work]," "straightforward combination of known techniques," "no new insight beyond marginal improvement."

---

## G6. Cherry-Picking / Narrow Evaluation

**Triggers when**: Results only hold under specific favorable conditions. Missing sensitivity analysis, limited scale, narrow task/dataset coverage without acknowledgment.

**Example concerns that map here**: "Only tested on one dataset," "missing sensitivity analysis," "results may not generalize," "narrow evaluation scope," "cherry-picked examples."

---

## G7. Overclaiming

**Triggers when**: Claims exceed what the evidence supports in scope or certainty. Different from G1 (which is about missing evidence); G7 is about the gap between what's shown and what's claimed.

**Example concerns that map here**: "Overstates generality of findings," "claims broad applicability but tests narrow setting," "language suggests certainty that data doesn't support."
