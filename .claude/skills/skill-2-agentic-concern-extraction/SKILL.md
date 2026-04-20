---
name: skill-2-agentic-concern-extraction
description: "Extracts a structured concern sheet from agentic review outputs. Use when building concern alignment data for a paper."
---

# Skill 2 — Extract Agentic Concerns (Result Dir → Concern Sheet)

## Goal
Given one paper × one method × one version result directory, extract an **agentic concern sheet**:
- concerns from review.md + adversarial_brief.md + gates.md + scorecard.md,
- normalized severities (level + addressability + mechanism),
- which concerns were decisive for the verdict,
- decision drivers (what drove the verdict) + non-decisive mentions (observed but not weighted).

## Inputs
- Directory containing: `summary.yaml`, `review.md`, `adversarial_brief.md`, `gates.md`, `scorecard.md` (and `debate.md` if present)
- Optional (panel method): `champion.md`, `skeptic.md`, `panel_verdict.md`
- Optional (Phase-0): `lit_search/tags.yaml` (only for provenance if the review cites it)

## Procedure

### 1. Read `summary.yaml`
- Extract: verdict, score, confidence, decisive_reasons, failed_gates.
- These establish the verdict context.

### 2. Parse `review.md`
- **Decisive reasons** → `decision_drivers` (with polarity, evidence, linked_concern_ids).
- **Major concerns** → `concerns` with severity level=major, decisive=true/false based on whether listed in decisive reasons.
- **Minor concerns** → `concerns` with severity level=minor, decisive=false.

- **Origin fields (if present)** → Preserve provenance for each concern.
  - If a concern includes lines like `Origin: skeptic` and `Origin pointer: skeptic bullet #2`, store:
    - `concern.origin`
    - `concern.origin_pointer`
  - If a concern was informed by a literature precedent from a `<!-- BEGIN LITERATURE EXAMPLES -->` block in a skill file, set `origin: lit_example` and `origin_pointer` to the skill file and precedent title (e.g., `origin_pointer: "skill-03, ToolChain*"`).
  - If missing, omit these fields.
- **One-paragraph summary** → scan for value claims (especially positive mentions of the paper's contribution). These become `mentions` (polarity=pro_accept), capturing things the system observed but did not treat as decisive. Important for diagnosing "mentioned but not weighted" failures.
  - **Hard rule**: Do NOT store substantive negative critiques as mentions with polarity=pro_reject. Any negative point that identifies a specific flaw, gap, or limitation belongs in `concerns`, not `mentions`. Mentions are for positive observations the system noted but didn't weight as decisive.
- **Above-the-line reason** (if ACCEPT) → becomes a `decision_driver` with polarity=pro_accept.
- **Debate summary** (if present) → extract winning argument as additional context.

### 3. Parse `adversarial_brief.md`
- Each adversarial point becomes a concern candidate.
- Map disposition to severity:
  - "Accepted as major concern" → level=major or fatal (check if binding rule applied).
  - "Accepted as minor concern" → level=minor.
  - "Refuted" → do NOT include as a concern (it was considered and dismissed).
  - "Partially refuted" → level depends on which part was accepted.
- If binding rule was triggered (e.g., "mandatory REJECT per adversarial escalation"):
  - Set `severity.mechanism = binding_rule`.
  - Mark as `decisive: true`.
- Source: `adversarial_brief`.

### 4. Parse `gates.md` and `scorecard.md`
- Any gate **FAIL** → concern with `source=gates`, `severity.level=fatal`, `severity.mechanism=gate_fail`.
- Any gate **CAUTION** → concern with `source=gates`, `severity.level=major`, note which dimensions were capped.
- Scorecard dimensions scored **<3** → concern candidates with `source=scorecard`, describing why the dimension was scored low. Include `dimension_impact`.
- Scorecard dimensions scored **=3 with notable "why not 4" justification** → only include if the justification maps to a specific concern not already captured.

### 5. Deduplicate
- Merge duplicates across sources by shared issue. Keep the highest-severity version.
- Preserve `source_detail` showing all sources that flagged the concern.
- Preserve `origin` / `origin_pointer` when present; if merged concerns have conflicting origins,
  keep the most decision-relevant one and mention the others in `source_detail`.
- Example: if adversarial_brief point 1 and review major concern #1 both flag "trivially defensible," merge into one concern with `source: adversarial_brief` and `source_detail: "Adversarial brief point 1 + review major concern #1"`.

### 6. Normalize severity
- `severity.level`: fatal / major / moderate / minor / unknown.
  - Map from review language: "High-severity" → fatal or major; "Medium-severity" → moderate; "addressable" → typically major with addressability=addressable.
- `severity.addressability`: unresolved / addressable / unknown.
  - "addressable" = the review explicitly says this can be fixed (e.g., "run one more experiment").
  - "unresolved" = the review treats this as a fundamental or structural issue.
  - "unknown" = severity classification is "(unknown)" in the review.
- `severity.mechanism`: the rubric rule that caused this severity assignment.
  - `binding_rule`: adversarial escalation binding rule at 75.0.
  - `gate_fail`: gate failure.
  - `gate_caution`: gate CAUTION with dimension cap.
  - `score_threshold`: concern pushed score below 75.0.
  - `debate`: debate resolved this concern's impact on verdict.
  - `none`: no specific mechanism; standard review judgment.

### 7. Tag and dimension-impact
- Apply 1–3 tags from the seed vocabulary.
- Assign `dimension_impact`: which scorecard dimensions this concern affected (A through H).

### 8. Quality checks
- Every concern must trace to a specific passage in the review outputs (source + source_detail).
- Decision_drivers must match `summary.yaml` decisive_reasons.
- Mentions must NOT overlap with decision_drivers (they capture different things).
- Severity.mechanism must be accurate — check whether binding rules, gates, or debate actually triggered.

### 9. Panel runs (if `champion.md` / `skeptic.md` exist)

If the method is `panel` (or panel artifacts exist), ensure origin provenance is not lost:

- Extract at least:
  - Skeptic’s decisive reject reason as a major concern with `origin: skeptic`.
  - Champion’s “Biggest weakness” as a concern with `origin: champion`.

If those issues already appear in `review.md`, prefer the `review.md` phrasing but keep origin pointers.

## Output
Emit YAML conforming to `AgenticConcernSheet` schema (see `calibration/concern_alignment/schemas/agentic_concern_sheet.schema.yaml`).
