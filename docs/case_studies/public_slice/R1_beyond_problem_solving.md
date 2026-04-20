# Case Study R1: Beyond Problem Solving

**Paper**: Beyond Problem Solving: A Three-Space Probe of LLM Critical Thinking
**Venue**: ACL ARR 2025 (preferred AACL)
**Scores**: 2 / 2 / 3.5 (AC: 2.5 Borderline Findings)
**Ground Truth**: REJECTED

> *Verdict-inference note: per-paper verdicts shown below are inferred from each system's review by our extraction pipeline (native for both System A configurations; inferred for the other four); System M reviews additionally contain coordination artifacts that make verdict inference structurally unreliable for that configuration. A follow-up audit re-read all 54 reviews in this slice with two independent raters using alternative inference rules. On this paper (which the venue rejected): pipeline 1/6 accept → audited 0/6 accept, 4/6 reject, 1 AMBIGUOUS (System L · GPT-4o — raters disagreed on tone), 1 UNRELIABLE (System M). The pipeline's sole accept disappears under audit: rater-2 read L · GPT-4o as acceptance-leaning while rater-1 read it as rejection-leaning, and both gates came back AMBIGUOUS. See the demo's Verdict Sensitivity panel (Named Papers segment) for the full per-system breakdown.*

This paper tests whether automated reviewers can recognize three well documented issues in a benchmark submission: a decorative theoretical framing, a narrow operationalization of the target construct, and evaluator circularity.

---

## Official Concerns Driving the Rejection

The AC meta review identifies three decisive blockers:

- **O1 (decisive blocker)**: "The Three-Space Theory is prominently introduced but not tightly integrated with the experimental design; the specific metrics are not matched to the three spaces." One official reviewer wrote verbatim that the "three-space theory appears flashy but insubstantial."
- **O2 (decisive blocker)**: The study "equates critical thinking solely with detecting deliberately introduced inconsistencies, overlooking broader aspects."
- **O3 (decisive blocker)**: "Using GPT-4o to evaluate other models' responses risks bias," since GPT-4o is used for both question generation and response classification.

The paper is a resubmission (LLM Spark, rejected at ICLR 2025 with 5/8/5/3) and concurrent work (GSM-DC at EMNLP 2025) covers overlapping ground.

---

## How Baselines Handled the Paper

Observational notes on the published baseline reviewers evaluated on this submission (see `data/reviews/public_slice/` for raw outputs):

- **AI Scientist (Claude and GPT-4o runs)**: Produces a small number of concerns centered on benchmark construction and evaluation rigor. Tends to recommend reject on this paper, though reasoning stays at the surface of "results not convincing enough" rather than identifying the theory-experiment disconnect specifically.
- **Liang et al. (Claude and GPT-4o runs)**: Generates a very low concern count; the zero-shot prompt does not drive the model to enumerate the three decisive blockers.
- **OAR**: Raises a broader set of concerns, most centered on statistical methodology and presentation rather than the decorative-framing issue.
- **MARG (GPT-4o)**: Produces a high-volume concern list that includes several items overlapping O1 and O3, with variable severity assignment.

The baselines diverge primarily on how explicitly they articulate the theory-experiment mismatch and the evaluator circularity. Some match O3 directly; others surface the same observation as a generic "evaluation design" note.

---

## What This Paper Reveals About Baseline Behavior

The three decisive blockers are structural (a framework that can be stripped without losing the empirical contribution, a construct narrowed to inconsistency detection, a single model used on both sides of an evaluation loop). Recognizing them requires reasoning about paper structure rather than checklist scoring. The baselines evaluated on this paper diverge on whether they surface all three, only a subset, or adjacent issues without naming the underlying cause.
