---
name: skill-5b-semantic-edge-verification
description: "Semantically verifies all match graph edges and unmatched concerns using audit worksheets. Produces structured override judgments. Use after Skill 5a worksheet generation."
---

# Skill 5b — Semantic Edge Verification

## Goal
Verify **all strict (exact/partial) match graph edges** and **all unmatched concerns** by reading the audit worksheet produced by Skill 5a. The worksheet provides side-by-side evidence; this skill provides independent semantic judgment. Produces structured override judgments that feed back into `compute_alignment_metrics.py`.

## Why this skill exists
Match graph construction (Skill 3) is an LLM-generated artifact and benefits from an independent second-pass review. This skill provides that verification layer, catching label errors before they propagate into downstream metrics.

This skill reads a pre-generated **audit worksheet** (produced by `scripts/generate_audit_worksheet.py` via Skill 5a) that lays out evidence neutrally — concern texts copied verbatim from source YAMLs, match labels, severities, and Jaccard scores side by side. The worksheet ensures the verifier sees the raw evidence without having framed it.

The verifier also has access to source files (concern sheets, match graphs, paper PDFs) for deeper context when the worksheet alone is insufficient.

## Ground-truth isolation
The sub-agent performing verification MUST NOT see:
- Official verdict (accepted/rejected)
- Error type (TP/TN/FP/FN)
- `ground_truth.yaml`
- Any file containing per-paper calibration outcomes

The sub-agent sees ONLY: audit worksheets, concern texts, match graph edge rationale, and paper PDF content.

**Note**: The audit worksheet header shows the official verdict for context. This is acceptable — the verifier judges edge quality, not paper quality. However, the verifier must not use the verdict to bias edge judgments (e.g., "this is an accepted paper so the agentic REJECT concerns must be phantoms").

## Inputs
- Audit worksheets (`calibration/concern_alignment/reports/worksheets/{version}/{method}/{paper}.md`) — produced by Skill 5a
- Match graph files (`calibration/concern_alignment/match_graphs/{version}/{method}/{paper}.yaml`) — for deeper context
- Official concern sheets (`calibration/concern_alignment/official/{paper}.yaml`) — for deeper context
- Agentic concern sheets (`calibration/concern_alignment/agentic/{version}/{method}/{paper}.yaml`) — for deeper context
- Paper PDFs (`papers/{paper}.pdf`) — for context when judging concern matches and for phantom verification

## Procedure

### 1. Read the audit worksheet

Read the worksheet markdown for this (paper, method) pair. It contains:
- **Section 1**: All strict edges with side-by-side concern texts, current labels, rationale, Jaccard scores
- **Section 2**: All unmatched official concerns with candidate agentic comparisons
- **Section 3**: All unmatched agentic concerns with candidate official comparisons
- **Section 4**: Related edges (informational)

### 2. Verify ALL strict edges

For each strict edge in the worksheet:

1. **Read the concern texts** as presented in the worksheet (these are verbatim from source YAMLs).
2. **Read the edge rationale** shown in the worksheet.
3. **Note the Jaccard score** (if shown). Low Jaccard warrants extra scrutiny but is not dispositive.
4. **Judge match_type**: Are these concerns about the same underlying issue?

   **Guiding principle**: Two concerns match (exact or partial) when they are about the *same specific issue*, not merely the *same broad topic*. Ask: "Would a neutral reader, seeing both concern texts without labels, say these are complaints about the same thing?" If yes, they match. If they would say "these are in the same area but about different things," they are at best `related`.

   Match levels:
   - `exact`: same issue, same scope. If the paper authors fixed concern A, that would *necessarily* fix concern B.
   - `partial`: same issue family, different scope or sub-claim. The concerns share a root issue but target different facets or operate at different levels of specificity.
   - `related`: nearby topic, not the same issue. The concerns share a theme but target genuinely different defects.
   - `none`: unrelated concerns, edge should be removed.

   **Calibrate your judgment using these exemplars** — curated from edges validated by external audit across 5 rounds (41 papers, 684 edges). E1-E19 from Rounds 1-4; E20-E32 mined from Round 5 taxonomy analysis targeting the highest-error cells (scope_inflation: 59% of errors). Each shows two concern summaries, the correct verdict, and a one-sentence reason. Paper names are omitted to prevent anchoring on specific papers.

   #### Exemplars: Correct Matches (do not over-reject)

   **E1 (exact)**: Missing baselines
   - Official: "missing stronger baselines (VAE-based, trajectory auto-encoders)"
   - Agentic: "only raw observations and outdated baseline compared, no modern methods"
   - Verdict: **correct (exact)** — same specific gap (missing modern baselines), same scope

   **E2 (exact)**: Qualitative explanations
   - Official: "evaluator-rewarder gap explanation mostly qualitative"
   - Agentic: "speculative causal explanations not validated"
   - Verdict: **correct (exact)** — same complaint (qualitative explanations lack empirical support), different wording

   **E3 (partial)**: Core mechanism validity
   - Official: "core assumption (subsequence = abstraction) is a questionable heuristic"
   - Agentic: "missing flat-sequence ablation to disentangle the contribution"
   - Verdict: **correct (partial)** — same issue family (is the core mechanism valid?), different angle (conceptual challenge vs missing experiment)

   **E4 (partial)**: Instance of broader pattern
   - Official: "unexplained performance variance across tasks"
   - Agentic: "specific task X shows persistently poor performance"
   - Verdict: **correct (partial)** — agentic concern is one specific instance of the official's broader pattern. Use `partial` when the narrower concern addresses one facet of the broader one. Contrast with E15 where the *agentic* concern is the broader one — same structural relationship, same verdict (partial).

   **E5 (exact)**: Evaluation metric validity
   - Official: "image quality metrics have no ground truth for the claimed phenomenon"
   - Agentic: "PSNR/FID against pre-event images measures rendering continuity, not physical correctness"
   - Verdict: **correct (exact)** — identical specific methodological concern about metric validity

   #### Exemplars: Tricky Correct (resist over-skepticism)

   **E6 (partial)**: Theory caveat clarity vs experimental validation
   - Official: "key proposition relies on a local approximation, conditions not clearly stated"
   - Agentic: "theory-practice gap — no experiments validate the large-beta regime the theory assumes"
   - Verdict: **correct (partial)** — same issue family (theory-practice disconnect), but the official wants clearer caveat *statements* while the agentic wants empirical *validation*. These require different author fixes → `partial`, not `exact`.

   **E7 (partial)**: Same root issue, different evidence demands
   - Official: "training data quality confound — no control for data filtering vs streaming format"
   - Agentic: "training data undergoes multi-stage filtering; unclear if gains come from data quality or method"
   - Verdict: **correct (partial)** — both target the same confound (data quality vs method contribution) but one asks for a specific control experiment while the other raises it as a broader concern. Same issue family, different specificity → `partial`. Do NOT downgrade to `related` just because they request different evidence.

   **E8 (exact)**: Same coverage gap
   - Official: "insufficient coverage of proprietary models in experiments"
   - Agentic: "missing evaluation on key proprietary models"
   - Verdict: **correct (exact)** — same specific coverage gap despite minor detail differences in which models are named

   **E9 (exact)**: Format-algorithm confound
   - Official: "comparison uses different training procedures (SFT vs GRPO), confounding format with algorithm"
   - Agentic: "format-algorithm confound: answer-only models use SFT while thinking models use GRPO"
   - Verdict: **correct (exact)** — identical specific confound identified with near-identical framing

   #### Exemplars: Wrong Matches (same topic, different issue)

   **E10 (wrong_match)**: Prior-work characterization vs novelty
   - Official: "prior methods DO support unconditional generation" (factual correction about prior work)
   - Agentic: "contribution is assembly of known techniques" (novelty critique)
   - Verdict: **wrong_match** — correcting a factual mischaracterization of prior work vs judging the novelty of the proposed method are fundamentally different concerns

   **E11 (wrong_match)**: Readability vs overclaiming
   - Official: "notation-heavy paper hard to follow" (readability/presentation)
   - Agentic: "title overclaims the contribution" (content framing)
   - Verdict: **wrong_match** — readability and title framing are unrelated even though both fall under "presentation"

   **E12 (wrong_match)**: Data diversity vs baseline diversity
   - Official: "extremely limited number of test scenes" (data/scene diversity)
   - Agentic: "narrow baseline set — only two methods compared" (comparison method diversity)
   - Verdict: **wrong_match** — adding more test scenes would not fix the baseline gap, and adding more baselines would not fix the scene gap

   **E13 (wrong_match)**: Experimental realism vs evaluation scope
   - Official: "simulated/offline setting rather than real-time interaction" (experimental realism)
   - Agentic: "evaluation limited to a single family of tasks at small scale" (scope)
   - Verdict: **wrong_match** — the realism of the experimental setup and the breadth of evaluation are different limitations

   **E14 (wrong_match)**: Different figures, different complaints
   - Official: "Figure 3 contradicts the paper's claimed degradation patterns"
   - Agentic: "Figures 1-2 use single-example visualizations"
   - Verdict: **wrong_match** — different figures with different complaints (contradictory evidence vs insufficient sample size)

   #### Exemplars: Tricky Wrong (look like matches but are not)

   **E15 (wrong_type, exact→partial)**: Broad concern subsumes narrow concern
   - Official: "stability variance not presented" (specific missing analysis)
   - Agentic: "no error bars, confidence intervals, or multi-seed runs across all datasets" (broader statistical rigor)
   - Verdict: **wrong_type** — the agentic concern subsumes the official one. The official is one specific instance of the agentic's broader complaint. Use `partial` not `exact`. Same structural relationship as E4 (broad ↔ narrow), same verdict — regardless of which side (official or agentic) is broader.

   **E16 (wrong_type, exact→partial)**: Same scope family, different missing items
   - Official: "no planning tasks evaluated"
   - Agentic: "no tasks requiring global-from-start reasoning (summarization, long-range proofs)"
   - Verdict: **wrong_type** — both say evaluation scope is too narrow but name different missing task types → `partial`

   **E17 (wrong_type, partial→related)**: Different evaluation families
   - Official: "confound control and ablation sufficiency"
   - Agentic: "variance/error bars not reported"
   - Verdict: **wrong_type** — these are genuinely different issue families despite both being "evaluation rigor." Confound control requires different experiments than variance reporting. Contrast with E7 where two concerns share a root issue (data quality confound) — this boundary requires checking whether the concerns demand the *same type of fix* or fundamentally different ones.

   **E18 (wrong_type, partial→related)**: Different evaluation sub-topics
   - Official: "limited experiment diversity (only 2 test objects)"
   - Agentic: "user study underpowered (N=10, no statistical tests)"
   - Verdict: **wrong_type** — experiment diversity and user study rigor are different sub-topics of evaluation → `related`, not `partial`

   **E19 (wrong_type, partial→related)**: Metric diversity vs statistical rigor
   - Official: "using only one evaluation metric (e.g., ASR) is overly simplistic and limits analysis depth"
   - Agentic: "no confidence intervals, significance tests, or multi-run reporting"
   - Verdict: **wrong_type** — these are `related`, not `partial`. Both concern evaluation quality, so they are not unconnected (`none`). But metric diversity (which metrics) and statistical rigor (how rigorously to report them) are different defects requiring different fixes. Adding more metrics would not fix missing error bars, and vice versa. Use `related` when concerns share a broad topic but target distinct defects.

   #### Exemplars: Scope Inflation (the #1 error pattern — one concern bundles extras)

   Scope inflation occurs when one concern (usually agentic) includes the other's complaint *plus* additional independent demands. The system over-matches by crediting the overlapping part and ignoring the extras. These exemplars teach the boundary between rhetorical elaboration (same issue, keep `exact`) and genuine broadening (different fix-actions, downgrade to `partial`).

   **E20 (wrong_type, partial→exact)**: Elaboration does not change the issue — Eval Rigor
   - Official: "validation metric is circular — uses model's own outputs as proxy"
   - Agentic: "circular validation metric restated with additional confound language"
   - Verdict: **wrong_type** — should be `exact`, not `partial`. The agentic adds rhetorical elaboration but targets the identical defect. The core complaint (circular metric) is the same; the extra language is restatement, not a separate fix-action. Do NOT downgrade to `partial` just because one side uses more words. Contrast with E21.

   **E21 (wrong_type, exact→partial)**: Genuine broadening adds independent fix-actions — Eval Rigor
   - Official: "no human evaluation of output realism"
   - Agentic: "human validation needed: realism assessment + correctness checking + safety audit"
   - Verdict: **wrong_type** — should be `partial`, not `exact`. The agentic bundles three genuinely independent evaluation dimensions. Fixing realism evaluation would NOT fix correctness or safety checking — each requires different study design. When the agentic adds fix-actions that are independent of the official's request, it's `partial`. Contrast with E20.

   **E22 (wrong_type, exact→partial)**: Bundled evaluation defects — Eval Rigor
   - Official: "single benchmark insufficient for the claimed generality"
   - Agentic: "single benchmark + no statistical significance testing + no error analysis"
   - Verdict: **wrong_type** — should be `partial`, not `exact`. The single-benchmark complaint overlaps, but the statistical-rigor and error-analysis demands are independent fix-actions. Adding more benchmarks would not add significance tests. Classic scope inflation: shared core + independent extras → `partial`.

   **E23 (wrong_type, exact→partial)**: Different thresholds of satisfaction — Eval Rigor
   - Official: "no experiments; contribution is purely theoretical"
   - Agentic: "experiments are toy-scale: synthetic data, no real workloads, no runtime comparison"
   - Verdict: **wrong_type** — should be `partial`, not `exact`. The official would be satisfied by *any* experiments. The agentic would not be satisfied by toy experiments — it demands realistic workloads. Different thresholds of satisfaction for the same broad gap → `partial`.

   **E24 (wrong_type, exact→partial)**: Positioning vs technique-level novelty — Novelty
   - Official: "closest prior work X already handles similar tasks"
   - Agentic: "combination of known techniques is incremental"
   - Verdict: **wrong_type** — should be `partial`, not `exact`. The official targets positioning against a specific named prior. The agentic targets technique-level novelty broadly. Demonstrating advantage over prior work X would not address the technique-combination incrementality argument, and vice versa. Different novelty defects within the same domain.

   **E25 (wrong_type, exact→partial)**: Conceptual differentiation vs familiar components — Novelty
   - Official: "must differentiate conceptually from specific prior system Y"
   - Agentic: "novelty limited — combines familiar components from the literature"
   - Verdict: **wrong_type** — should be `partial`, not `exact`. Same pattern as E24: specific-positioning vs broad-technique novelty. Conceptual differentiation from system Y would not fix the familiar-components argument.

   **E26 (wrong_type, exact→partial)**: Broad equation analysis vs specific ablation — Theory
   - Official: "key equation needs deeper analysis of when it helps vs hurts"
   - Agentic: "must ablate one specific assumption in the equation"
   - Verdict: **wrong_type** — should be `partial`, not `exact`. The official asks for *any* analysis of the equation's behavior. The agentic demands one particular ablation. The ablation would partially address the concern but the official wants broader analysis. Broader-ask vs narrower-demand → `partial`. Contrast with E27.

   **E27 (wrong_type, exact→partial)**: Broad validation vs specific causal evidence — Theory
   - Official: "core assumptions need broader validation beyond the current proof setting"
   - Agentic: "missing specific causal evidence for the claimed benefit"
   - Verdict: **wrong_type** — should be `partial`, not `exact`. Opposite specificity direction from E26: official is broad, agentic is narrow. The specific causal evidence is one way to validate but doesn't cover the full scope the official wants. scope_inflation works in both directions (broad→narrow and narrow→broad).

   #### Exemplars: Other Mined Patterns (from taxonomy analysis)

   **E28 (wrong_type, partial→related)**: Metric diversity vs variance reporting — Eval Rigor
   - Official: "need more diverse evaluation metrics beyond the current set"
   - Agentic: "missing variance and uncertainty reporting across experiments"
   - Verdict: **wrong_type** — should be `related`, not `partial`. Which metrics to use vs how rigorously to report them are different evaluation defects. Adding metrics would not fix missing error bars. Reinforces E19 in a different context.

   **E29 (wrong_match)**: Readability vs limited novelty — Clarity/Content
   - Official: "paper not self-contained — relies on reader knowing cited works"
   - Agentic: "limited novelty — contribution is incremental given existing theory"
   - Verdict: **wrong_match** — official is about exposition quality (readability). Agentic is about contribution significance (novelty). Improving exposition would not fix the novelty concern, and vice versa. Even though both relate to how the paper positions itself relative to prior work, they are different issue families. Reinforces E11.

   **E30 (wrong_type, partial→related)**: Different theoretical properties — Theory
   - Official: "convergence rate bounds may not be tight"
   - Agentic: "approximation quality degrades with sequence length"
   - Verdict: **wrong_type** — should be `related`, not `partial`. Both are theoretical concerns but target different mathematical properties: convergence rate tightness vs approximation quality degradation. Different proofs would be needed for each. Within theory, distinguish *which* theoretical property is questioned.

   **E31 (wrong_severity)**: Same issue, severity gap too large — Eval Rigor
   - Official: "modest gains without statistical analysis [major]"
   - Agentic: "missing statistical significance tests [moderate]"
   - Verdict: **wrong_severity** — match_type is correct (`partial`) but severity gap is 2 levels (major vs moderate). The official frames it as a core evaluation flaw; the agentic frames it as a reporting gap. When match_type is right but severity is off by ≥2 levels, flag `wrong_severity`.

   **E32 (wrong_match)**: Mechanistic explanation vs comparative evaluation — Causal Understanding
   - Official: "missing analysis of why the method produces good results"
   - Agentic: "missing comparison showing output quality vs established alternatives"
   - Verdict: **wrong_match** — both relate to understanding quality, but one asks for mechanistic explanation (why) and the other asks for comparative benchmarking (how much). These require fundamentally different evidence — causal analysis vs performance tables.

   **After reviewing exemplars, apply this two-step test to each edge:**
   1. Identify the *specific defect* each concern targets (not the broad topic area).
   2. Ask: would fixing defect A necessarily address defect B? If yes → `exact`. If they share a root issue but need different fixes → `partial`. If they are in the same broad area but target different defects → `related`.
5. **Judge judgment_alignment** (if match_type is exact or partial):
   - `aligned`: both treat it as weakness/concern
   - `inverted`: same fact, opposite normative conclusion
   - `mixed`: partially aligned
   - `n/a`: match too weak
6. **Judge severity_alignment** (if match_type is exact or partial):
   - Compare official `severity` (string) with agentic `severity.level` (string)
   - Severity order: minor=0, moderate=1, major=2, fatal=3
   - Gap ≤1 → `match`; gap ≥2 with agentic lower → `under`; gap ≥2 with agentic higher → `over`
   - `n/a`: match too weak
7. **Determine verdict and action**:
   - Verdict: `correct` / `wrong_match` / `wrong_type` / `wrong_severity` / `multiple_errors`
   - Action: `confirmed` (no change) / `reclassified` (labels changed) / `removed` (edge deleted)
   - **Verdict/action consistency rule**: The verdict and action MUST reflect the actual override labels:
     - If `override_match_type` differs from `original_match_type` → verdict includes `wrong_type`
     - If `override_severity_alignment` differs from original `severity_alignment` → verdict includes `wrong_severity`
     - If both differ → verdict is `multiple_errors`
     - If neither differs → verdict is `correct`, action is `confirmed`
     - `action: reclassified` whenever ANY override label differs from the original
     - Do NOT set `verdict: correct` + `action: confirmed` when you have changed any label. This causes the correction to be silently dropped by downstream metrics.

### 3. Verify ALL unmatched concerns

For each unmatched official concern shown in the worksheet:
- Read the concern text and the candidate agentic comparisons shown
- If a match exists that Skill 3 missed, record it as a `missed_match` with recommended match_type and severity_alignment
- If no match exists, confirm as `correctly_unmatched`

For each unmatched agentic concern shown in the worksheet:
- Read the concern text and the candidate official comparisons shown
- If a match exists, record it as a `missed_match`
- If no match exists, confirm as `correctly_unmatched` (true phantom)
- For phantoms with explicit numeric claims, optionally check the paper PDF to assess whether numbers are grounded

### 4. Verify flagged phantoms (if flagged queue available)

If `semantic_audit.py` produced a flagged phantom queue, verify each:

1. **Read the agentic concern text** from the worksheet or concern sheet.
2. **Read the paper PDF**: Focus on tables, figures, and results sections where numbers typically appear.
3. **Search for unfound numbers in context**: The heuristic uses substring matching which misses:
   - Numbers in figures and plots (not in extractable text)
   - Tables with complex formatting
   - Numbers mentioned with different precision (e.g., "93%" vs "93.3%")
   - Numbers derived from computation
4. **Judge the phantom**:
   - `grounded`: numbers are in the paper — the extraction heuristic missed them
   - `hallucinated`: numbers do not appear anywhere in the paper
   - `policy_artifact`: numbers come from the review system's scoring formula
   - `inconclusive`: cannot determine with available evidence

### 5. Write overrides YAML

Write the override file to:
```
calibration/concern_alignment/overrides/{version}/semantic_overrides.yaml
```

The file must conform to `calibration/concern_alignment/schemas/semantic_override.schema.yaml`.

```yaml
schema_version: v1
version: "{version}"
generated_by: skill_5b_claude_code

edge_overrides:
  - method: baseline
    paper: example_paper
    official_id: O2
    agentic_id: A4
    original_match_type: exact
    override_match_type: partial
    override_judgment_alignment: aligned
    override_severity_alignment: under
    verdict: wrong_type
    action: reclassified
    rationale: "Both concerns address novelty overlap with prior work, but O2 focuses on RAG poisoning literature overlap while A4 targets broader prior art. Same family, different scope."
    confidence: high

missed_matches:
  - method: baseline
    paper: example_paper
    official_id: O5
    agentic_id: A3
    recommended_match_type: partial
    recommended_judgment_alignment: aligned
    recommended_severity_alignment: match
    rationale: "Both flag insufficient ablation controls. O5 targets confound isolation; A3 targets specific missing ablation for component X."
    confidence: medium

phantom_judgments:
  - method: baseline
    paper: example_paper
    agentic_id: A5
    unfound_numbers: ["93.3", "0.0"]
    judgment: grounded
    rationale: "93.3% appears in Table 2 row 3 (ASR before defense); 0.0% appears in same table."
    confidence: high
    evidence_location: "Table 2, p. 7"

verification_summary:
  total_edges_verified: 25
  total_unmatched_verified: 40
  error_counts:
    false_matches: 3
    type_errors: 2
    severity_errors: 1
    missed_matches: 4
  error_rates:
    false_match_rate: "12.0%"
    type_error_rate: "8.0%"
    severity_error_rate: "4.0%"
    missed_match_rate: "10.0%"
  skill26_health: needs_improvement  # see thresholds below
  papers_verified:
    - paper: example_paper
      method: baseline
      edges_verified: 5
      unmatched_verified: 8
      errors_found: 2
```

### Skill 3 health diagnostic (advisory)

After computing error rates, include a `skill26_health` field in `verification_summary`. This is a diagnostic on how well Skill 3 is performing — it does NOT block the pipeline. Overrides are always applied.

| Metric | healthy | needs_improvement | needs_overhaul |
|--------|---------|-------------------|----------------|
| False match rate | <5% | 5-10% | >10% |
| Total error rate (false_match + type + severity) | <15% | 15-25% | >25% |
| Missed match rate | <20% | 20-35% | >35% |

The **worst** threshold across all three metrics determines the health label.

- **healthy**: Skill 3 is producing reliable match graphs
- **needs_improvement**: Elevated error rate — note in report, consider adding more false-match patterns to Skill 3
- **needs_overhaul**: Skill 3 is producing unreliable match graphs — prioritize improving Skill 3 rules before the next version

## Integration

Overrides are **always applied** regardless of Skill 3 health — they only improve metrics.

The override file feeds into `compute_alignment_metrics.py --overrides`:
- `confirmed` edges: no metric change (logged for audit trail)
- `reclassified` edges: match_type/judgment_alignment/severity_alignment updated before metric computation
- `removed` edges: deleted from matches list; affected concerns become unmatched
- `missed_matches`: new edges added to the match graph
- Phantom judgments: reported in the override summary section

After verification, always proceed to metrics:
```bash
python scripts/fix_severity_alignment.py ...
python scripts/compute_alignment_metrics.py --overrides calibration/concern_alignment/overrides/{version}/semantic_overrides.yaml
```

## Quality checks

1. **No ground-truth leakage**: Verify the sub-agent prompt does not contain verdicts, error types, or paper outcomes.
2. **Evidence-grounded**: Every override rationale must cite specific concern text or paper location.
3. **Conservative**: When uncertain, prefer `confirmed` (keep original) over `reclassified`. Default to `inconclusive` for phantoms.
4. **Complete coverage**: ALL strict edges and ALL unmatched concerns must be verified. Do not skip items because they "look fine."
5. **Independent judgment**: Judge each edge on its own merits. Read the concern texts in the worksheet first, then check the match graph rationale. Do not anchor on Skill 3's judgment.
6. **Worksheet-first**: Base your initial judgment on the worksheet evidence. Only read source files for deeper context when the worksheet alone is ambiguous.

## Invocation

```bash
# Step 1: Generate advisory flags
python scripts/semantic_audit.py --output-queue tmp/queue.yaml

# Step 2: Generate worksheets (Skill 5a agent runs the script + validates)
# Produces: calibration/concern_alignment/reports/worksheets/{version}/{method}/{paper}.md

# Step 3: Run verification (Skill 5b agent reads worksheets + judges)
# Produces: calibration/concern_alignment/overrides/{version}/semantic_overrides.yaml
# Includes skill26_health diagnostic in verification_summary

# Step 4: Apply severity fixes + compute metrics (always — overrides always improve)
python scripts/fix_severity_alignment.py ...
python scripts/compute_alignment_metrics.py --overrides calibration/concern_alignment/overrides/{version}/semantic_overrides.yaml
```
