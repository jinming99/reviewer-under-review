---
name: skill-4-alignment-aggregate
description: "Performs cross-paper pattern mining on concern alignment data and proposes rubric revisions. Use after completing per-paper concern matching."
---

# Skill 4 — Aggregate Concern Alignment and Propose System Fixes

## Goal
Aggregate alignment data across many papers to identify:
- systematic detection misses (by tag / issue_type),
- systematic severity bias (under / over),
- judgment inversions (feature vs fatal),
- method-level and version-level deltas,
and propose concrete, prioritized modifications to the review system.

## Inputs
- Set of OfficialConcernSheet YAMLs
- Set of AgenticConcernSheet YAMLs (per method / version)
- Set of ConcernMatchGraph YAMLs
- Ground truth decisions + error types (TP/TN/FP/FN per paper × method)

## Procedure

### 0. Lint gate
Before aggregation, run `scripts/lint_concern_alignment.py` on the data set. If any issues are found (severity sign errors, related-match severity set, edge cap violations, unmatched-list inconsistencies, pro_reject factors in positive_factor_matches), fix them before proceeding. Do not compute metrics on unclean data.

### 0.5. Pre-severity derivation
Severity calibration should be computed **directly from raw severity levels** on matched edges (official `severity` string vs agentic `severity.level` string), NOT from the hand-labeled `severity_alignment` field in match graphs. This avoids propagating labeling errors. Use the tolerance rules from Skill 3 §5: ±1 level = match, fatal requires fatal.

### 0.6. Observability-aware positive-factor recall
When computing positive-factor recall for accepted papers, report two variants:
- **All**: recall over all official pro_accept drivers.
- **Pre-rebuttal**: recall over only those drivers with `observable_stage: pre_rebuttal`. This is the fair comparison — the agentic system reviews pre-rebuttal papers and cannot observe rebuttal/post-discussion factors.

### 0.7. Semantic audit + verification (optional, targeted)
Run `scripts/semantic_audit.py --output-queue <path>` to generate a structured inspection queue of the most suspicious artifacts:
- **Low-overlap strict edges**: exact/partial edges whose official and agentic texts have very low Jaccard similarity (content tokens). These are candidates for "partial-vs-related" label drift.
- **Phantom numeric groundedness misses**: strict-unmatched agentic concerns with explicit numbers that don't appear in the paper PDF text.

This is a **deterministic pre-filter**, not a verifier. To verify edges, run:
1. **Skill 5a** (`meta_eval/.claude/skills/skill-5a-worksheet-generation/SKILL.md`) — generates audit worksheets via `scripts/generate_audit_worksheet.py`
2. **Skill 5b** (`meta_eval/.claude/skills/skill-5b-semantic-edge-verification/SKILL.md`) — reads worksheets and produces independent semantic verification overrides (`calibration/concern_alignment/overrides/{version}/semantic_overrides.yaml`)

Then re-run metrics with overrides applied:
```bash
python scripts/compute_alignment_metrics.py --overrides data/overrides/{version}/semantic_overrides.yaml
```

Ground-truth isolation: the Skill 5 sub-agent MUST NOT see official verdicts, error types, or `ground_truth.yaml`.

### 1. Build the aggregate table

Flatten all match edges + unmatched concerns into a single table:

```
| paper | error_type | off_id | agen_id | match | judgment | severity | off_tags | off_issue_type | agen_source | agen_mechanism |
```

Include unmatched rows:
- Official misses: `agen_id = null`, `match = miss`
- Agentic phantoms: `off_id = null`, `match = phantom`

### 2. Compute per-method and per-version aggregates

For each method and version present under the data root:

| Metric | Computation |
|--------|-------------|
| Issue recall (strict) | exact+partial matches / total official concerns |
| Issue recall (post-rebuttal) | exact+partial matches / official concerns with severity_post != resolved |
| Issue recall (loose) | exact+partial+related / total official concerns |
| Issue precision | matched agentic / total agentic concerns |
| Decisive negative recall | AC blockers flagged / total AC blockers |
| Decisive severity accuracy | AC blockers flagged with correct severity / AC blockers flagged |
| Judgment inversion rate | inverted matches / total matches |
| Severity under-rate | under matches / total matches |
| Severity over-rate | over matches / total matches |
| Mean phantom rate | unmatched agentic / total agentic (averaged across papers) |
| Cluster recall (strict) | *Diagnostic.* Clusters from official tags (connected components, excluding generic tags). A cluster is "hit" if any member has a strict match. Reduces brittleness from over-atomization and 2-edge cap. |
| Phantom policy rate | *Diagnostic.* Share of strict-unmatched agentic concerns with `severity.mechanism != "none"`. Isolates policy/process-triggered phantoms from content phantoms. |
| Phantom numeric groundedness | *Diagnostic, lower-bound.* Among phantoms with explicit numbers, fraction whose numbers appear in paper PDF text. High rate suggests "valid-but-unmentioned," not hallucination. |

### 3. Stratify analysis

**By error type** (TP / TN / FP / FN):
- Do FPs have different alignment patterns than FNs?
- Hypothesis: FPs have low severity on real concerns (under-weighting). FNs have high severity on non-issues (over-weighting or phantom concerns driving REJECT).
- **Calibrated finding**: Severity calibration matters more than detection. The system finds concerns but weights them wrong. Under-severity → FP; over-severity → FN. The direction of miscalibration predicts the error type (FP-FN severity asymmetry is the strongest diagnostic signal).

**By issue_type** (conceptual / empirical / framing):
- Compute miss rate by issue_type.
- Hypothesis: empirical concerns have high recall, conceptual and framing concerns have low recall.
- **Known gap**: LLM reviewers systematically under-detect framing concerns. No dedicated framing-alignment skill exists. When analyzing framing misses, flag this as a structural gap and track whether proposed interventions improve framing recall.

**By tag**:
- Miss rate per tag: which concern topics are systematically undetected?
- Severity bias per tag: which topics are systematically over/under-weighted?
- Phantom rate per tag: which topics does the system generate without official support?

**By agentic source** (adversarial_brief / gates / scorecard / review_major / debate):
- Which sources generate the most phantoms?
- Which sources have the best judgment alignment?
- Which sources are most likely to cause severity inversions?

**By mechanism** (binding_rule / gate_fail / gate_caution / score_threshold / debate / none):
- Which mechanisms cause judgment inversions?
- What is the correct-vs-incorrect rate for each mechanism?
- Hypothesis: binding_rule has high inversion rate and should be modified.

### 4. Identify top-N actionable patterns

Rank findings by:
1. **Frequency**: how many papers are affected?
2. **Impact on verdict accuracy**: does fixing this pattern change the binary verdict?
3. **Feasibility**: can this be fixed with a targeted rubric change, or does it require architectural changes?

### 5. Propose concrete interventions

For each top-N pattern, produce a proposal:

```yaml
pattern_id: P1
description: "binding_rule at 75.0 causes judgment inversions"
frequency: "4/N papers affected"
error_types_affected: [FN]
evidence:
  - paper: "{paper_slug}"
    detail: "Same observation treated as feature by officials, fatal by binding rule"
  - paper: "[other examples]"
root_cause: "Adversarial escalation binding rule mechanically converts unrefuted High points to REJECT at 75.0"
proposed_fix:
  file: "rubric/decision_policy.md"
  change: "Condition binding rule on judgment alignment — require that the unrefuted point be normatively negative (a flaw), not just factually correct. Add: 'If the adversarial point is factually correct but the observation can be reasonably interpreted as neutral or positive (e.g., demonstrating a fixable blind spot), it does not trigger mandatory REJECT.'"
expected_impact: "Reduce FN rate on borderline accepted papers. May increase FP rate if poorly calibrated."
risks: "Could weaken the rule's ability to catch genuine FPs where the adversarial point is a real flaw."
test_papers: ["{paper_slug}", ...]
```

### 6. Prioritize proposals

Rank by: `(frequency × verdict_impact) / implementation_risk`

Group into:
- **Safe patches**: high confidence, low risk, clear evidence (e.g., fixing a broken rule)
- **Calibration changes**: medium confidence, require testing on pilot set
- **Structural additions**: new skills or gates, require validation on larger set

### 7. Output

Produce two artifacts:

**Report** (`calibration/concern_alignment/reports/improvement_proposals.md`):
- Summary statistics (tables of metrics by method, version, error type)
- Top-N patterns with evidence
- Proposals ranked by priority
- Recommended testing plan

**Structured proposal list** (`calibration/concern_alignment/reports/proposals.yaml`):
- Machine-readable list of proposed changes for tracking

## Quality checks
- Every proposal must cite at least 2 papers as evidence (avoid overfitting to single cases).
- Every proposal must include expected risks and test papers.
- Proposals that change weights or thresholds must include the mathematical impact analysis (weight changes are often inert for uniform-3 profiles).
- Cross-check proposals against calibrated findings noted in this skill, `rubric/review_qc.md`, and `CHANGELOG.md` to avoid repeating past mistakes.
