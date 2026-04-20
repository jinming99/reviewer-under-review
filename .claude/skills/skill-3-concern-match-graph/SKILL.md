---
name: skill-3-concern-match-graph
description: "Builds a match graph between official and agentic concern sheets with alignment metrics. Use after extracting both concern sheets."
---

# Skill 3 — Build Concern Match Graph (Official ↔ Agentic)

## Goal
Given an official concern sheet and an agentic concern sheet for the same paper/method/version, produce a **match graph** — explicit edges between concerns that represent the same underlying issue, annotated with judgment alignment and severity calibration.

## Why match-graph-first (not tag overlap)
- Two concerns can share tags but be different issues.
- The same issue can be phrased differently and get different tags.
- The hardest errors are judgment inversions (same fact, opposite conclusion) — tags can't capture those.
- The match graph separates "did you see it?" from "did you interpret it correctly?" from "did you weight it correctly?"

## Inputs
- OfficialConcernSheet YAML (one per paper)
- AgenticConcernSheet YAML (one per paper × method × version)

## Procedure

### 1. Normalize each concern into a canonical issue statement
- For each concern (official and agentic), write a one-sentence canonical `issue` description.
- Focus on the underlying issue, not the phrasing. E.g.:
  - Official: "Could filtering out unicode characters be a simple way to defend?" → "Unicode character filtering defeats the steganographic attack"
  - Agentic: "Attack is trivially defensible — character filtering reduces unsafe rate from 93.3% to 0.0%" → "Unicode character filtering defeats the steganographic attack"
  - Same canonical issue → match.

### 2. Propose candidate matches
- For each agentic concern, identify the top 1–3 official concerns it could match.
- For each official concern, identify the top 1–3 agentic concerns it could match.
- Work from both directions to avoid missing matches.

### 3. Choose match_type
- `exact`: same underlying issue, same scope. Both sides are talking about the same specific problem.
  - Example: both say "evaluation uses only AdvBench" → exact.
  - **Scope test**: If the paper authors fixed concern A, would that *necessarily* fix concern B? If yes → `exact`. If not → `partial` at best.
- `partial`: same issue family but different scope or sub-claim. The concerns are clearly related but address different facets.
  - Example: O4 "no definition of unreliable source" ↔ A3 "construct validity of ASR metric" — both are about whether the evaluation measures what it claims, but one is about concept definition and the other is about metric design.
  - **Broad ↔ narrow**: A broad official concern ("evaluation is insufficient") matched to a narrow agentic sub-concern ("missing baseline X") is `partial`, not `exact`. The agentic concern addresses one instance of the broader issue.
  - **Same family, different abstraction level**: Both about "novelty" but one about framing of prior work and the other about magnitude of contribution → `partial`.
- `related`: nearby topic but not the same issue. Use sparingly — mainly to document near-misses.
  - Example: A5 "predictable findings" is *related* to O2 "RAG overlap" (both say "this isn't new") but targets different things (findings vs. problem formulation).
- **Upgrade partial→exact when**: Both concerns identify the same specific gap with different wording. Test: would a neutral third party reading both descriptions say "these are the same complaint"? If yes → `exact`.

**False match patterns — do NOT match these (use `related` at most):**

These patterns were identified by external audit across 18 papers. Each represents a distinct failure mode where thematic overlap is mistaken for issue identity.

1. **"Prior work characterization" ↔ "method novelty"**: Misrepresenting prior work (factual accuracy about others' methods) is distinct from novelty criticism (whether the new contribution is sufficient). Example: "prior methods DO train unconditional policies" ≠ "contribution is assembly of known techniques."
2. **"Missing specific baseline X" ↔ "results lack statistical rigor"**: Missing a comparator is not the same as missing error bars, variance reporting, or significance tests. Both are "evaluation" concerns but require different author fixes.
3. **"Writing quality/presentation" ↔ "overclaiming"**: Notation heaviness, readability, and presentation clarity should never be matched to content-level concerns like title overclaiming, missing baselines, or theoretical limitations.
4. **"Same component, different complaint"**: Two concerns that mention the same method component (e.g., GRPO, CPD, latency) but target different defects (design flaw vs weak contribution vs confound vs overhead). Same component name is necessary but not sufficient — the underlying complaint must also align.
5. **"Evaluation scope" ↔ "evaluation methodology"**: Missing datasets/domains (scope) is distinct from missing ablations/controls (methodology). Both are "evaluation" but different fixes.
6. **"Broad theme match"**: Two concerns both touch "evaluation quality" or "theory limitations" but target genuinely different specific issues. Thematic area overlap alone does not justify even a `related` match. Both concerns must target the same specific defect or the same missing evidence.
7. **General test**: If the two concerns would require *different fixes* by the authors, they are not `exact` and may not even be `partial`.

### 4. Label judgment_alignment
- `aligned`: both treat it as a weakness/concern, even if severity differs. The normative conclusion is the same direction.
- `inverted`: same fact but opposite normative conclusion. One side sees it as a flaw; the other sees it as a feature or non-issue.
  - Example: "Trivially defensible" — officials reframed as "demonstrates a blind spot worth exposing," agentic treated as "fatal flaw." Same observation, opposite implication.
- `mixed`: partially aligned, partially inverted. Rare — usually means the concern should be split.
- `n/a`: match is too weak to assess judgment alignment.

### 5. Label severity_alignment
- Compare official `severity` (string: fatal/major/moderate/minor) with agentic `severity.level` (string: same enum).
- For official concerns with `ac_treatment: reframed_feature`, treat the effective severity as "non-blocking" (lower than minor) for comparison purposes.
- For official concerns with `ac_treatment: accepted_limitation`, keep the coded severity as-is — the concern is real and its severity is accurate. The AC simply judged it non-blocking for the verdict. If the agentic system matches the severity, that's correct alignment.
- `n/a`: match type is `related` or too weak to compare. Always use `n/a` for related matches.

**Decision rules** (severity order: minor=0, moderate=1, major=2, fatal=3):

| Gap (agentic − official) | Label |
|---------------------------|-------|
| 0 (same level)            | `match` — **always**. Never label same-severity as under/over. |
| ±1 level                  | `match` — within tolerance. E.g., major↔moderate, moderate↔minor. |
| ≤ −2 (agentic much lower) | `under` — e.g., official=major, agentic=minor. |
| ≥ +2 (agentic much higher) | `over` — e.g., official=minor, agentic=major. |

**Common mistakes to avoid:**
- Do NOT label same-severity edges as `under` or `over` because one side is decisive and the other isn't. Decisiveness is about the concern's role in the verdict, not its severity level.
- Do NOT label ≥2-level gaps as `match`. Major↔minor and fatal↔moderate are never within tolerance.
- Do NOT conflate `ac_treatment` (resolved, unresolved, decisive_blocker) with severity. A "major (resolved)" concern still has severity=major for comparison purposes. Whether it was resolved in rebuttal affects the verdict, not the severity label.

### 6. Write rationale
- Brief explanation (1-2 sentences) of why the match exists and why the judgment/severity annotation was chosen.
- This is for human reviewers to verify the matching quality.

### 7. Match positive decisive factors (for accepted papers)
For accepted papers, the AC's decisive factor is often **positive** ("practical demonstration value on real APIs"). This requires a separate matching step because the agentic system represents positive factors differently from concerns.

**Format**: Include **one row per official pro_accept driver** in `positive_factor_matches`. Use `match_type: none` for drivers the agentic system did not capture. This makes the denominator for positive-factor recall explicit in the YAML itself.

**Hard rules**:
- Include **only** `polarity: pro_accept` drivers. Do NOT include `polarity: pro_reject` drivers in `positive_factor_matches` — those belong in the concern matches section.
- Do NOT invent post-rebuttal or post-discussion factors that the agentic system could not observe. Only match against factors that were observable pre-rebuttal unless the official driver explicitly existed pre-rebuttal.

Match official `ac_decision_drivers` with `polarity: pro_accept` against:
  - Agentic `above_the_line_reason` (from summary.yaml)
  - Agentic `mentions` with `polarity: pro_accept` (from agentic concern sheet)
  - Agentic `decision_drivers` with `polarity: pro_accept` (for ACCEPTs)

Use the same match_type / judgment_alignment labels. Severity_alignment is not applicable for positive factors.

Record unmatched positive factors in `unmatched_positive_factors` (DEPRECATED — prefer encoding misses as `match_type: none` rows in `positive_factor_matches`).

This step is critical: for accepted papers, the system may correctly flag no fatal concerns but still miss *why* the paper deserves acceptance.

### 8. Record unmatched concerns
- `unmatched_official`: official concern IDs with no **strict** (exact/partial) match edge. Related-only matches still count as strict-unmatched — they indicate the system noticed the topic area but did not detect the specific issue.
- `unmatched_agentic`: agentic concern IDs with no **strict** (exact/partial) match edge. Related-only matches still count as strict-unmatched (phantom concerns).

**Schema enforcement**: A concern that has ONLY `related` edges and no `exact` or `partial` edges MUST appear in the unmatched list. Do not omit concerns from unmatched lists because they have a `related` edge — `related` is a near-miss annotation, not a match.

## Matching rules
1. **Prefer one-to-one.** Each concern can appear in at most **2 match edges**. If you need more, the concern is too broad — split it.
2. **Don't force matches.** If an official concern has no plausible agentic counterpart, leave it unmatched. Better an explicit miss than a spurious match.
3. **When in doubt, use `partial` or `related`** rather than `exact`. Exact means the same specific issue.
4. **Ambiguous cases** (typically 1-2 per paper): make the call, document the rationale, move on. The aggregate analysis is robust to individual matching errors.

## Output
Emit YAML conforming to `ConcernMatchGraph` schema (see `calibration/concern_alignment/schemas/match_graph.schema.yaml`).

## Example

```yaml
schema_version: v1
paper: example_paper
version: v1
method: example_method

matches:
  - official_id: O1
    agentic_id: A2
    match_type: exact
    issue: "Simulation-based testing with forcibly injected adversarial content is unrealistic"
    judgment_alignment: aligned
    severity_alignment: under  # official: fatal, agentic: major-addressable
    rationale: "Both flag simulation fidelity. Agentic accepts 'lower bound' framing; AC explicitly rejects it as 'inherently unrealistic.'"

  - official_id: O2
    agentic_id: A4
    match_type: exact
    issue: "Core vulnerability already validated in RAG poisoning literature"
    judgment_alignment: aligned
    severity_alignment: under  # official: major, agentic: minor
    rationale: "Both identify RAG overlap. Agentic classifies as minor; officials and AC treat as major novelty concern."

  - official_id: O4
    agentic_id: A3
    match_type: partial
    issue: "Construct validity of evaluation framework"
    judgment_alignment: aligned
    severity_alignment: under  # official: major, agentic: unknown→addressable
    rationale: "O4 is about undefined 'unreliable source' concept; A3 is about ASR metric validity. Both are construct concerns but different facets."

  - official_id: O8
    agentic_id: A1
    match_type: exact
    issue: "LLM-as-judge evaluation has limited human validation"
    judgment_alignment: aligned
    severity_alignment: over  # official: moderate, agentic: major
    rationale: "Both flag narrow judge validation scope. Agentic treats as major; officials treat as moderate."

unmatched_official: [O3, O5, O6, O7, O9]
unmatched_agentic: [A5, A6]
```
