---
name: skill-5a-worksheet-generation
description: "Generates audit worksheets for match graph verification by running generate_audit_worksheet.py and validating its output. Use before Skill 5b verification."
---

# Skill 5a — Audit Worksheet Generation

## Goal
Run `scripts/generate_audit_worksheet.py` to produce side-by-side evidence worksheets for all match graphs in a version/method, then validate the output is complete and accurate. These worksheets are consumed by Skill 5b for independent semantic verification.

## Why this skill exists
Verbatim reproduction of concern text is essential so the Skill 5b verifier works from the source record rather than a paraphrase. A Python script copies text directly from the source YAML; this skill wraps the script to handle failures gracefully, validate output completeness, and ensure the worksheets are ready for independent verification.

## Inputs
- Version string (e.g., `v1`)
- Method(s) to process (one or all system configurations present under the data root)
- Optional: flagged queue from `semantic_audit.py --output-queue` (advisory Jaccard annotations)

## Procedure

### 1. Run semantic_audit.py for advisory flags (optional)

If a flagged queue doesn't already exist:

```bash
python scripts/semantic_audit.py --output-queue tmp/queue.yaml
```

This produces Jaccard similarity scores that get annotated onto worksheet edges for the verifier's reference. The queue is **advisory only** — Skill 5b verifies ALL edges regardless.

### 2. Run the worksheet script for each (method, paper) pair

For batch mode (recommended):
```bash
python scripts/generate_audit_worksheet.py \
  --version {version} --method {method} --all \
  --output-dir calibration/concern_alignment/reports/worksheets/{version}/{method}/ \
  --flagged-queue tmp/queue.yaml
```

For single paper:
```bash
python scripts/generate_audit_worksheet.py \
  --version {version} --method {method} --paper {paper} \
  --output calibration/concern_alignment/reports/worksheets/{version}/{method}/{paper}.md \
  --flagged-queue tmp/queue.yaml
```

### 3. Check for script failures

If the script exits with an error:
- Read the error message (the script reports per-paper errors to stderr)
- Common failure modes:
  - **FileNotFoundError**: Missing match graph, official sheet, or agentic sheet — check paths
  - **ValueError (ID resolution)**: A concern ID in the match graph doesn't exist in the concern sheet — likely a schema change or ID typo in the match graph
  - **YAML parse error**: Malformed YAML in a source file
- Fix the underlying issue and re-run

### 4. Validate worksheet completeness

For each generated worksheet, verify:

1. **Edge count**: The number of strict edges in Section 1 matches the count of exact/partial edges in the source match graph
2. **Unmatched counts**: Section 2 and Section 3 list exactly the concerns from `unmatched_official` and `unmatched_agentic` in the match graph
3. **Verbatim accuracy**: Spot-check 2-3 concern texts against the source YAML to confirm they were copied verbatim (not paraphrased)
4. **No truncation**: Worksheets should contain all 4 sections (strict edges, unmatched official, unmatched agentic, related edges if any)

If discrepancies are found, report them and investigate whether the script has a bug or the source data is inconsistent.

### 5. Output

Write all worksheets to:
```
calibration/concern_alignment/reports/worksheets/{version}/{method}/
```

Report summary:
- Total worksheets generated
- Any failures (paper slug + error)
- Any validation issues found
- Total strict edges, unmatched official, unmatched agentic across all papers

## Output format

Each worksheet is a markdown file with this structure:

```
# Audit Worksheet: {paper} / {method} / {version}

## Section 1: Strict Edges (exact/partial)
  - Per edge: side-by-side concern texts, severities, tags, match labels,
    rationale, Jaccard score, blank verdict fields

## Section 2: Unmatched Official Concerns
  - Per concern: text, severity, tags, top-5 candidate agentic comparisons
    ranked by Jaccard, blank verdict field

## Section 3: Unmatched Agentic Concerns
  - Per concern: text, severity, source, decisive flag, tags, top-5 candidate
    official comparisons ranked by Jaccard, blank verdict field

## Section 4: Related Edges (informational)
  - Related edges listed for context, not scored
```

## Quality checks

1. **No paraphrasing**: All concern texts must come verbatim from source YAMLs. The script handles this, but validate.
2. **Complete coverage**: Every strict edge and every unmatched concern must appear. No sampling.
3. **Correct paths**: Verify the script is reading from the right version/method directories.
