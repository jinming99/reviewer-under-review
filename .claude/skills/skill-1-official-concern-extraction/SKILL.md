---
name: skill-1-official-concern-extraction
description: "Extracts a structured concern sheet from official OpenReview reviews. Use when building concern alignment data for a paper."
---

# Skill 1 — Extract Official Review Concerns (OpenReview → Concern Sheet)

## Goal
Given OpenReview PDFs (reviews + meta-review), extract an **official concern sheet**:
- atomic concerns (issue units),
- severity,
- whether they were resolved in rebuttal,
- AC/meta-review treatment (decisive blocker vs resolved vs dismissed/feature),
- AC decision drivers (positive + negative),
- flexible tags and issue_type.

## Inputs
- OpenReview PDF text (reviews + meta-review; rebuttal if available)
- Optional: final decision, decision type (oral/spotlight/poster), reviewer score changes

## Procedure

### 1. Anchor on the meta-review
- Extract AC's decisive rationale as `ac_decision_drivers` with polarity (`pro_accept` / `pro_reject`).
- Identify any AC-explicit decisive blockers and store their IDs in `ac_decisive_negative_ids`.
- For accepted papers, note what the AC praised as the key contribution.
- For rejected papers, note what the AC identified as the fatal flaw(s).

### 2. Extract atomic concerns
- For each reviewer, list each distinct criticism as a separate concern.
- Keep each concern **single-issue** (avoid bundling). If a reviewer raises two issues in one paragraph, split them.
- Store a short `verbatim` quote (roughly 25 words or fewer) or near-verbatim paraphrase.
- Record `raised_by` with reviewer IDs.
- If multiple reviewers raise the same issue, create ONE concern with multiple `raised_by` entries.

### 3. Assign severity (pre-rebuttal)
- `fatal`: undermines validity/claims in a way that blocks acceptance absent major redesign.
- `major`: substantial weakness likely to affect acceptance unless convincingly addressed.
- `moderate`: real concern but not typically blocking on its own.
- `minor`: polish-level, presentation, or "nice to have."
- Use the reviewer's own severity language if available (some venues label weaknesses as "major" or "minor").

### 4. Code rebuttal/meta outcome
- `resolved_in_rebuttal`: true / false / null (if unknown).
- `rebuttal_resolution`: brief description of how it was resolved (if applicable).
- `ac_treatment` (the key field for ground truth):
  - `decisive_blocker`: AC explicitly identified this as driving the rejection.
  - `unresolved`: concern was raised and not resolved in rebuttal; may or may not have been decisive.
  - `resolved`: concern was raised but satisfactorily addressed in rebuttal (per AC judgment).
  - `accepted_limitation`: concern stands but AC explicitly accepts it as non-blocking (e.g., cost-justified scope limitation, acknowledged but not fatal).
  - `dismissed`: AC explicitly dismissed the concern as not relevant or not significant.
  - `reframed_feature`: AC or reviewers reinterpreted the weakness as a positive (e.g., "trivially defensible → demonstrates a blind spot").
  - `not_mentioned`: AC did not address this concern in the meta-review.
  - `unknown`: insufficient information to determine AC treatment.
- `decisive`: true if this concern was THE reason (or one of the reasons) for the final decision.
- If AC explicitly says "inherently unrealistic", "fundamental", "fatal flaw" → `decisive_blocker`.
- If AC says "convincingly addressed", "no longer a concern" → `resolved`.
- If AC says "remains a limitation" but accepts the paper anyway, or "acknowledged by cost constraints" → `accepted_limitation`. The concern is real and the severity stands, but it didn't block the decision.

### 5. Tagging
- Apply 1–3 flexible tags from the seed vocabulary. Create a new tag if needed (don't force fit).
- Add `issue_type` — a high-level axis orthogonal to tags:
  - `conceptual`: concerns about the core idea, contribution depth, or theoretical framework (e.g., "trivially defensible," "not fundamentally different from RAG poisoning," "no definition of unreliable source")
  - `empirical`: concerns about experimental scope, additional benchmarks, missing baselines, statistical rigor (e.g., "single benchmark," "missing Claude models," "no human study")
  - `framing`: concerns about how the paper positions its contribution, title-content alignment, overclaiming (e.g., "title says red-teaming but it's a static benchmark," "claims to solve X but actually addresses Y")

### 6. Extract critical references (if present)

Scan all reviews and the meta-review for **specific papers or literature cited as critical to the assessment**. Not all papers will have these — only extract when reviewers explicitly name papers that influenced their judgment.

For each critical reference, record:
- `id`: CR1, CR2, ... (sequential)
- `title`: full paper title (as identifiable as possible for search matching)
- `short_name`: how reviewers refer to it (e.g., "LATS", "ToolChain*")
- `cited_by`: which reviewer(s) mentioned it
- `role`: why it was cited — one of:
  - `missing_comparison` — reviewer says paper should have compared against this
  - `novelty_precedent` — reviewer cites this as evidence the contribution is incremental
  - `methodological_basis` — reviewer says this is the real foundation/prior work
  - `positive_positioning` — reviewer cites this favorably to support the paper
  - `missing_citation` — reviewer flags missing citation (not necessarily critical)
  - `benchmark_precedent` — reviewer compares to an existing benchmark/dataset
- `decisive`: did this reference influence the accept/reject decision?
- `concern_ids`: which concerns reference this paper (optional)
- `verbatim`: near-verbatim quote from reviewer citing this paper (≤25 words)

**What to extract**: Papers that reviewers argue should have been compared against, that establish the novelty baseline, or that the AC references when explaining the decision. Generic "see also" citations are not critical references.

**What NOT to extract**: The paper's own cited references unless a reviewer specifically argues they were inadequately addressed. Background citations mentioned in passing without bearing on the assessment.

Place the `critical_references` array after `ac_decision_drivers` and before `ac_decisive_negative_ids` in the output YAML.

### 7. Quality checks
- **No hallucinations**: every concern must have evidence in review/meta-review text.
- **No over-merging**: if in doubt, split concerns rather than merge.
- **Severity anchoring**: use reviewer's own language where possible; don't infer severity beyond what's stated.
- **AC treatment accuracy**: re-read the meta-review before coding `ac_treatment`. This is the most important annotation.
- **ac_decisive_negative_ids consistency**: every concern ID listed in `ac_decisive_negative_ids` MUST have `ac_treatment: decisive_blocker` and `decisive: true`. If there's a mismatch, re-read the meta-review and fix whichever field is wrong. The lint script (`lint_concern_alignment.py`) will catch this automatically.

## Output
Emit YAML conforming to `OfficialConcernSheet` schema (see `calibration/concern_alignment/schemas/official_concern_sheet.schema.yaml`).

## Example
See `calibration/concern_alignment/official/` for worked examples (available in local calibration data).
