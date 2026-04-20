# External LLM Verdict Inference — Batch Processing Instructions

## Context

You are the second rater in a two-rater verdict inference study. A first rater (Claude Code) is processing the same reviews independently. Your outputs will be compared for inter-rater reliability.

**Study goal:** For each AI-generated paper review, determine two things:
1. **Tone verdict**: What verdict does the review's tone and content imply? (ACCEPT / REJECT / AMBIGUOUS)
2. **Gate verdict**: Reading the raw review as primary source and the extracted concern sheet as supplementary structure, does the review identify enough fundamental issues to warrant rejection under a principled gate framework?

**Important**: For BOTH tasks, the **raw review text** is the primary input. The concern sheet is a structured extraction that may have missed concerns or miscategorized severity. Use it as a scaffold, but trust your own reading of the raw review when they conflict.

This package covers **9 papers × 6 system configurations = 54 reviews**, split into 3 batches. Slice: Named Papers public slice (calibration_set: public_slice, 9 papers). Do not reuse outputs from any previous audit; every review in this package must be freshly rated from its raw review text.

---

## What You Receive Per Batch

Each batch directory (`batch_01/` through `batch_03/`) contains:
- `batch_manifest.yaml` — list of papers and reviews in this batch
- `reviews/` — raw review text files (one per review: `{slug}__{system}_{model}.md`)
- `concern_sheets/` — extracted concern YAML files (one per review: `{slug}__{system}_{model}.yaml`)

Additionally, at the package level:
- `gate_definitions.md` — the 8 gate categories (G0–G7) with full definitions
- `worked_examples.md` — 6 annotated examples showing how to apply both methods (from an earlier audit on unrelated papers; use them as method calibration anchors only, not as data to carry forward)
- `output_schema.md` — exact CSV output format
- `ground_truth_metadata.yaml` — paper metadata (venue, decision) for the 9 papers in this package

---

## Task 1: Tone Verdict

For each review, read the raw review text and assess:

**Question:** Based on the review's overall tone and content, is the reviewer recommending ACCEPT, REJECT, or is it genuinely AMBIGUOUS?

**Guidelines:**
- Do NOT default to either verdict. Commit to the lean you detect.
- Consider: Are concerns fundamental (methodology, validity, novelty) or minor (clarity, missing refs)?
- Does the reviewer express enthusiasm or merely acknowledge the work?
- Are criticisms framed as blocking or addressable?
- A review that raises only moderate concerns with constructive language signals ACCEPT.
- A review that identifies fatal methodological flaws signals REJECT.
- AMBIGUOUS is reserved for genuinely balanced cases — most reviews lean one way.

**Output per review:**
- `tone_verdict`: ACCEPT | REJECT | AMBIGUOUS
- `tone_confidence`: high | medium | low
- `tone_signal`: one sentence explaining what drove your verdict

---

## Task 2: Gate Verdict

For each review, read the **raw review text** as the primary source, using the extracted concern sheet as supplementary structure. Identify all major or fatal concerns and classify each into the gate categories it triggers.

If the raw review contains a major concern that the concern sheet missed, add it to your gate classification (note it as "not in sheet" in per_concern_gates_json). If the concern sheet rates a concern as major but the raw review text suggests it's actually moderate, trust the raw review.

### Gate Classification Rules

Read each concern's TEXT (not just tags) and determine which gates it maps to:

- **G0**: Central claims not explicit/falsifiable
- **G1**: Claim–evidence mismatch (claim lacks direct supporting evidence, or evidence tests something else)
- **G2**: Baseline fairness (headline improvement depends on weak, missing, or unfair baselines)
- **G3**: Method not implementable (missing algorithm, hyperparams, splits)
- **G4**: Validity bugs / leakage / confounding (obvious threat that could invalidate the main result)
- **G5**: Novelty is trivially incremental
- **G6**: Cherry-picking / narrow evaluation
- **G7**: Overclaiming (claims exceed what evidence supports)

A concern may trigger 0, 1, or multiple gates. Only classify major/fatal concerns.

### Gate Verdict Rules

After classification, apply these rules in priority order:

1. **REJECT** if any concern has severity = fatal
2. **REJECT** if 2+ major/fatal concerns map to **fundamental gates** (G1, G2, G4, G5)
3. **ACCEPT** if 0 fundamental gate hits AND no fatal concern AND the review contains substantive acceptance reasons
4. **AMBIGUOUS** otherwise (1 fundamental hit, or 0 hits but no acceptance signal)

### What Counts as a "Positive Acceptance Signal"

Look in the concern sheet's `decision_drivers` for any entry with `polarity: "pro_accept"`. Also consider whether the raw review text contains explicit pro-accept language (e.g., "reasons for acceptance" sections with substantive content, enthusiastic endorsement, explicit recommendation).

**Output per review:**
- Per-concern gate classifications (concern_id → list of gates)
- `gate_verdict`: ACCEPT | REJECT | AMBIGUOUS
- `gate_reason`: one sentence explanation
- `fundamental_gate_hits`: count of major/fatal concerns in G1/G2/G4/G5
- `fatal_concern_present`: true/false

---

## Output Format

For each batch, produce a CSV file (`batch_NN_results.csv`) with these columns:

```
review_id, paper_slug, system, model, official_decision,
tone_verdict, tone_confidence, tone_signal,
gate_verdict, gate_reason, triggered_gates, fundamental_gate_hits, fatal_concern_present,
num_concerns, num_decisive_concerns, num_major_fatal_concerns,
has_accept_signal,
per_concern_gates_json,
structural_unreliable_flag, positive_tone_missed_flaws_flag
```

Where:
- `review_id`: use format `EXT9-NNN` zero-padded to 3 digits (e.g., `EXT9-001` … `EXT9-054`)
- `per_concern_gates_json`: JSON array like `[{"id":"A1","gates":["G1","G4"]},{"id":"A2","gates":[]}]`
- `structural_unreliable_flag`: YES if the review is structurally broken (e.g., multi-agent coordination artifacts instead of coherent review). All System M reviews should be evaluated for this.
- `positive_tone_missed_flaws_flag`: YES if the tone reads as ACCEPT but the gate analysis suggests REJECT (i.e., review sounds positive because it missed fundamental issues)

---

## Important Calibration Notes

1. **Neither method is calibrated to acceptance rate.** The ground truth is 50% accepted, 50% rejected. Your gate verdicts will likely reject more than 50% — that's expected and correct. The gate framework asks "does this review identify fundamental issues?" not "should this paper be accepted?"

2. **System M (GPT-4o) reviews are often structurally broken.** On comparable prior audits, System M reviews were frequently flagged as structurally unreliable. Expect similar patterns. Still assign verdicts, but flag them.

3. **System A has native verdicts.** System A reviews contain an explicit `Decision: Accept/Reject` field. For tone inference, this is the verdict. For gate inference, classify the concerns as usual.

4. **Be thorough on gate classification.** Read concern TEXT, not just tags — tag-based approaches have been observed to under-count fundamental gate hits by roughly 3× relative to semantic classification.

---

## What We Need Beyond Verdicts (for the report)

The outputs will be used for a detailed analysis section in the paper. We need not just verdicts but the reasoning and evidence behind them, so we can write a rich, validated account. Specifically:

### Per-review reasoning (captured in CSV columns)
- `tone_signal`: one sentence — but make it specific. "Review is generally positive" is not useful. "Review identifies 3 major concerns but frames all as addressable with specific suggestions" is useful.
- `gate_reason`: should reference the specific gate categories and concern count.
- `per_concern_gates_json`: this is critical for the report. Include ALL major/fatal concerns with their gate classifications. If you identified a concern from the raw review that wasn't in the sheet, add it with `"source": "raw_review"`.

### Per-batch summary (produce as a short text block at the end of each batch)
After completing each batch, write a 3-5 sentence summary noting:
1. How many reviews in this batch showed tone-gate divergence
2. Any papers where ALL 6 systems agree (interesting for calibration)
3. Any papers where systems maximally disagree (interesting for case studies)
4. Whether System M structural issues continued in this batch
5. Any surprising or notable patterns you noticed

### Aggregation across batches
All 3 batch CSVs should use the same column schema (output_schema.md) with no variation. Use `review_id` prefix `EXT9-` (e.g., `EXT9-001` … `EXT9-054`) so these outputs never collide with any prior audit CSV. Total expected: 54 rows across 3 batches (18 + 18 + 18).

### What the paper section will cover
We plan to write about:
1. **Method comparison**: How do tone vs gate verdicts differ systematically? Which claims change?
2. **Inter-rater reliability**: Cohen's kappa between you and Claude Code on the same reviews
3. **Sensitivity analysis**: headline numbers on this slice — do they survive method changes?
4. **Worked examples**: 4-6 specific reviews where methods diverge, with full reasoning chains
5. **The root observation**: Systems not trained to produce verdicts → uncalibrated concerns → verdict inference is inherently ambiguous → concern-level evaluation is more robust

Your per-review reasoning and per-batch summaries are the raw material for points 4 and 5. Be specific and evidence-grounded.
