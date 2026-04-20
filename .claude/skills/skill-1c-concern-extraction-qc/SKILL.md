---
name: skill-1c-concern-extraction-qc
description: "Independent quality check on a Skill 1b concern sheet. Reads the concern sheet + review PDF + paper PDF to verify consistency, catch hallucinations, and flag ambiguities. One QC agent per paper."
---

# Skill 1c — Independent Quality Check for Concern Extraction

## Goal
Given a concern sheet produced by Skill 1b, independently verify its quality by
reading the source documents (review PDF + paper PDF). This agent has NOT seen the
extraction process — it checks the output cold.

## Inputs
1. **Concern sheet YAML** produced by Skill 1b (the file to verify)
2. **Review/Forum PDF** (the source for concerns, rebuttals, meta-review)
3. **Paper PDF** (the evaluated version — for `addressed_in_pdf` verification)

## Procedure

### 1. Structural consistency checks

**1a. ac_decisive_negative_ids consistency**:
- Every concern ID in `ac_decisive_negative_ids` must have `ac_treatment: decisive_blocker` and `decisive: true`.
- Every concern with `ac_treatment: decisive_blocker` must appear in `ac_decisive_negative_ids`.
- Flag any mismatch.

**1b. Resolution field consistency**:
- If `addressed_in_pdf: true` AND `resolved_in_rebuttal: false` AND `ac_treatment: not_mentioned`:
  flag as **AMBIGUOUS** — fix exists in PDF but no reviewer/AC confirmation. Check: did the
  reviewer actually respond? Is the AC silent on this specific concern or silent overall (terse meta-review)?
- If `addressed_in_pdf: false` AND `resolved_in_rebuttal: true`: flag as **SUSPICIOUS** —
  claimed resolved but no evidence in PDF. Check the rebuttal: was it resolved via verbal
  clarification (acceptable) or did the author promise a PDF change that isn't there?
- If `pdf_is_revised: false` AND any concern has `addressed_in_pdf: true`: verify this is
  because the original submission already addressed it (reviewer may have missed existing
  content), not because the revision check failed.

**1c. Severity consistency**:
- Fatal-severity concerns should not have `ac_treatment: dismissed` or `accepted_limitation`
  (a fatal concern that's accepted as limitation suggests severity was wrong).
- Minor-severity concerns should not have `ac_treatment: decisive_blocker`.
- Flag any mismatches for re-evaluation.

**1d. ID sequence**: Concern IDs should be O1, O2, ... without gaps.

### 2. Hallucination spot-check

Select 3-5 concerns (prioritize fatal/major severity) and verify against the review PDF:
- Does the `verbatim` quote actually appear in the reviews?
- Does the `raised_by` reviewer ID match the reviewer who said it?
- Is the `text` (normalized concern statement) a fair representation of what the reviewer said?
- Flag any concern where the verbatim doesn't match or the concern appears fabricated.

### 3. Completeness check

Skim the review PDF for substantive concerns that may have been missed:
- Check each reviewer's "Weaknesses" section — were all weaknesses extracted?
- Check the meta-review — were all AC-cited issues captured as concerns?
- Minor omissions (truly minor, presentation-only concerns) are acceptable.
- Flag any missing major/fatal concerns.

### 4. PDF cross-verification spot-check

Select 2-3 concerns where `addressed_in_pdf: true` and verify:
- Does the cited section/table/figure actually address the concern?
- Is the evidence genuine (not just tangentially related text)?

Select 2-3 concerns where `addressed_in_pdf: false` and verify:
- Is the concern genuinely unaddressed in the PDF?
- Could the extractor have missed relevant content?

### 5. Concern Resolution Principle compliance

For each concern, verify the resolution status follows the principle:
- `resolved` requires reviewer/AC confirmation OR verified fix in PDF
- Author claims alone → should be `not_mentioned` (still-standing), NOT `resolved`
- Check that the default is still-standing, not resolved

## Output

```yaml
qc_result:
  forum_id: "{forum_id}"
  sheet_path: "{path to concern sheet}"
  overall_verdict: pass / pass_with_flags / fail

  structural_issues:
    - check: "ac_decisive_negative_ids consistency"
      status: pass / fail
      detail: ""
    - check: "resolution field consistency"
      status: pass / flag
      detail: ""
    # ... one per check

  hallucination_checks:
    - concern_id: O1
      status: verified / suspicious / hallucinated
      detail: ""
    # ... 3-5 spot checks

  completeness:
    missing_concerns: []  # list of missed concerns, if any
    detail: ""

  pdf_crosscheck:
    - concern_id: O3
      field: addressed_in_pdf
      claimed: true
      verified: true / false
      detail: ""
    # ... 4-6 spot checks

  resolution_principle:
    violations: []  # concern IDs where resolution status doesn't follow the principle
    detail: ""

  flags:
    - concern_id: O5
      issue: "ambiguous resolution — fix in PDF but reviewer silent"
      recommended_action: "human review"
    # ... any concerns needing human attention
```

## Verdicts

- **pass**: No structural issues, no hallucinations found, no missing major concerns, resolution principle followed.
- **pass_with_flags**: Structurally sound but has ambiguous cases or minor issues that need human attention. List all flags.
- **fail**: Hallucinated concerns found, missing major/fatal concerns, or structural inconsistencies that invalidate the sheet. Sheet needs re-extraction.
