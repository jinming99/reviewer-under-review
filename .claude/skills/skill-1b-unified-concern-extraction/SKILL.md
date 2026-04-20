---
name: skill-1b-unified-concern-extraction
description: "Extracts a structured concern sheet from official OpenReview reviews WITH paper PDF cross-verification. Determines per-concern resolution status by checking whether each concern is addressed in the evaluated PDF version. Replaces separate Skill 1 + revision check passes with a single unified pass."
---

# Skill 1b — Unified Concern Extraction with PDF Cross-Verification

## Goal
Given OpenReview PDFs (reviews + meta-review) AND the paper PDF, extract an **official concern sheet** with **per-concern resolution verification**:
- atomic concerns (issue units),
- severity,
- whether they were resolved in rebuttal,
- AC/meta-review treatment (decisive blocker vs resolved vs dismissed/feature),
- **whether each concern is addressed in the evaluated PDF** (cross-checked against paper content),
- AC decision drivers (positive + negative),
- flexible tags and issue_type.

This skill extends Skill 1 by adding paper PDF cross-verification. The output is
schema-compatible with `OfficialConcernSheet` (v1) plus additional per-concern fields
(`addressed_in_pdf`, `pdf_evidence`) and a top-level `pdf_is_revised` field.

## Inputs
- **Paper PDF** (the version the AI review system will evaluate — may be original submission, revised version, or camera-ready)
- **OpenReview PDF** (reviews + meta-review + author rebuttals rendered from the forum page)
- Optional: final decision, decision type (oral/spotlight/poster), reviewer score changes

## Procedure

### 0. Determine PDF version status (NEW — not in Skill 1)

Read the paper PDF and check:
- **Colored/highlighted text** (blue, red, orange) indicating revision markup
- **Post-submission content** (model names released after submission deadline, references to "reviewer feedback", "as suggested by Reviewer X")
- **Revision notes** or "changes from previous version" sections

Read the review/forum PDF and check:
- Author rebuttal comments explicitly mentioning "uploaded revised version", "updated manuscript", "changes highlighted in blue/red"
- AC or reviewer comments referencing "the revised version" or "updated paper"

Record:
- `pdf_is_revised`: true / false
- `revision_evidence`: one-line summary of evidence (or "no evidence of revision")

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

### 4b. Cross-verify against paper PDF (NEW — not in Skill 1)

For EACH concern extracted in Step 2, check the paper PDF:

**A. Is the concern addressed in the current PDF?**
- Look for added text, tables, experiments, clarifications that directly address the concern.
- Be specific: cite the section, page, table, or figure where the fix/addition appears.
- If no evidence of the fix in the PDF, record "no evidence in PDF."
- For concerns about missing content (e.g., "no ablation"): check if the ablation now exists.
- For concerns about methodology: check if the methodology was changed/clarified.

**B. Apply the Concern Resolution Principle:**

| Evidence | `resolved_in_rebuttal` | `ac_treatment` |
|---|---|---|
| Reviewer confirms resolved (raised score, said "addressed") | `true` | `resolved` |
| AC confirms resolved | `true` | `resolved` |
| Authors fixed it + fix visible in PDF + reviewer/AC silent | `true` | Keep existing code from Step 4 (likely `not_mentioned`) |
| Authors claim fixed but no evidence in PDF, reviewer/AC silent | `false` | `not_mentioned` (still-standing) |
| Nobody addresses it | `false` | `not_mentioned` |
| AC dismisses concern | — | `dismissed` |
| AC accepts as limitation | — | `accepted_limitation` |

**Key rule**: Author claims alone are insufficient for `resolved`. Reviewer/AC must
confirm, OR the fix must be verified in the evaluated PDF.

Record per concern:
- `addressed_in_pdf`: true / false
- `pdf_evidence`: "Section 5.3 adds ablation table for component X" or "no evidence in PDF"

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

### 7. Self-checks (before output)
- **No hallucinations**: every concern must have evidence in review/meta-review text.
- **No over-merging**: if in doubt, split concerns rather than merge.
- **Severity anchoring**: use reviewer's own language where possible; don't infer severity beyond what's stated.
- **AC treatment accuracy**: re-read the meta-review before coding `ac_treatment`. This is the most important annotation.
- **ac_decisive_negative_ids consistency**: every concern ID listed in `ac_decisive_negative_ids` MUST have `ac_treatment: decisive_blocker` and `decisive: true`. If there's a mismatch, re-read the meta-review and fix whichever field is wrong.

**Note**: Independent quality checks (cross-check consistency, hallucination spot-checks, ambiguity flagging) are performed by a separate Skill 1c agent. Do NOT skip concerns or over-edit based on self-doubt — output your best extraction and let the QC agent catch issues.

## Output
Emit YAML conforming to `OfficialConcernSheet` schema (see `calibration/concern_alignment/schemas/official_concern_sheet.schema.yaml`) with these additional fields:

**Top-level (new):**
- `pdf_is_revised`: boolean
- `revision_evidence`: string

**Per-concern (new):**
- `addressed_in_pdf`: boolean
- `pdf_evidence`: string

These additional fields are backward-compatible — the existing schema allows extra properties. When this skill replaces Skill 1, the schema will be updated to include them.

## Example
See `calibration/concern_alignment/official/` for worked examples of the base schema.
The new fields add to (not replace) the existing structure.
