# Baselines Comparison

> **Verdict-inference scope.** Verdict accuracy figures in this file reflect our extraction pipeline's interpretation of review tone or structure. Native verdicts are produced by both System A configurations (Opus and GPT-4o), which emit an explicit Decision field; for the other four configurations the verdict is inferred. The 48-paper table in §2 is single run (run 1) — it will not numerically match the homepage, which displays 3-run means. The 9-paper table in §3 is also single run (run 1). The paper appendix's sensitivity audit (covering a separate 48-paper safety/alignment benchmark) shows verdict-level numbers vary with inference method, while concern-level metrics — recall, FDR, decisive precision, phantom rates — do not. The audit has since been extended to the 9-paper public slice (54 reviews, same three-method two-rater design). Per-configuration flip rate on the public slice: System A · GPT-4o 0/9, System A · Opus 0/9, System L · GPT-4o 2/9, System L · Opus 0/9, System M · GPT-4o 7/9 (all to UNRELIABLE), System O · Opus 1/9. The direction matches the 48-paper benchmark on the main qualitative points: both native-verdict configurations (A · Opus and A · GPT-4o) are stable, System M is structurally unreliable throughout, and System L · GPT-4o remains one of the more tone-sensitive inferred configurations (the 9-paper slice is too small to rank it as the most sensitive overall). The demo's Verdict Sensitivity panel (Named Papers segment) has the full per-paper breakdown. System M reviews additionally contain multi-agent coordination artifacts that make verdict inference unreliable for that configuration regardless of method.

## 1. What this file compares

This file compares the **six released baseline configurations** that appear in the public snapshot:

- `System A · Opus`
- `System A · GPT-4o`
- `System L · Opus`
- `System L · GPT-4o`
- `System M · GPT-4o`
- `System O · Opus`

The comparison is intentionally split into two scopes:

1. the **48-paper benchmark context**, which is what the public site headline metrics refer to; and  
2. the **9-paper Named Papers slice**, which is where the public case studies live.

## 2. 48-paper benchmark context

| Method | 48-paper accuracy | Accepted-paper accuracy | Rejected-paper accuracy | Avg strict recall | Avg phantom rate |
|---|---|---|---|---|---|
| System A · GPT-4o | 50.0% | 0.0% | 100.0% | 19.9% | 46.0% |
| System A · Opus | 45.8% | 4.2% | 87.5% | 43.6% | 48.9% |
| System L · GPT-4o | 54.2% | 62.5% | 45.8% | 24.2% | 39.4% |
| System L · Opus | 50.0% | 0.0% | 100.0% | 39.4% | 41.7% |
| System M · GPT-4o † | 56.2% | 58.3% | 54.2% | 31.4% | 60.1% |
| System O · Opus | 54.2% | 29.2% | 79.2% | 13.9% | 79.8% |

†System M: all 48 reviews contain multi-agent coordination artifacts; verdict inference is unreliable regardless of method (see paper appendix on the verdict inference audit).

### Read this table carefully

- The 48-paper numbers describe the full calibration benchmark used by the public demo headline. They are **single run (run 1)**; the homepage displays 3-run means.
- These numbers are suitable for high-level positioning in the README and on the homepage, with the run-basis difference noted.
- They are **not** the same as the public raw-artifact slice in the zip, which contains full end-to-end artifacts for nine named papers.
- Verdict accuracy is native for both System A configurations (Opus and GPT-4o), which emit an explicit Decision field; for the other four configurations it is inferred from review text by our extraction pipeline. Concern-level metrics (recall, phantom rate) are independent of the inference method.

## 3. 9-paper Named Papers slice

| Method | Named Papers accuracy | TP/TN/FP/FN | Strict recall | Loose recall | Precision | Phantom rate | Decisive recall |
|---|---|---|---|---|---|---|---|
| System L · GPT-4o | 77.8% | 6/1/1/1 | 22.4% | 27.0% | 69.4% | 30.6% | 29.2% |
| System M · GPT-4o | 44.4% | 3/1/1/4 | 33.0% | 43.9% | 57.6% | 42.4% | 29.2% |
| System O · Opus | 44.4% | 2/2/0/5 | 13.2% | 27.7% | 28.6% | 71.4% | 0.0% |
| System A · Opus | 33.3% | 1/2/0/6 | 32.7% | 38.0% | 48.4% | 51.6% | 62.5% |
| System L · Opus | 22.2% | 0/2/0/7 | 30.3% | 38.7% | 63.1% | 36.9% | 50.0% |
| System A · GPT-4o | 22.2% | 0/2/0/7 | 20.2% | 26.1% | 60.4% | 39.6% | 25.0% |

### What the public slice adds

The nine-paper slice is where the concern-level stories become legible. It includes well-known accepted papers, borderline accepted papers, and two rejected papers. The slice is small, but it is diagnostic: it shows how different systems can agree or disagree for very different reasons.

## 4. Behavioral profiles to use consistently across public surfaces

### System A · Opus
- Strongest claim: comparatively high strict recall and the highest decisive recall in the public slice.
- Limitation: rejects most accepted papers in both the 48-paper benchmark and the nine-paper slice.
- Public framing: **high detection, weak calibration**.
- One-line description: Finds many of the right problems, but often treats non-blocking concerns as rejection-worthy.

### System A · GPT-4o
- Strongest claim: relatively low phantom rate on the nine-paper slice.
- Limitation: reject-heavy behavior with weak accepted-paper performance.
- Public framing: **brief and selective, but too skeptical**.
- One-line description: Concise and selective, but too often lands in reject-by-default behavior.

### System L · Opus
- Strongest claim: strong precision and good unresolved-concern recall.
- Limitation: implicit reject-heavy behavior despite balanced-sounding reviews.
- Public framing: **balanced prose, reject-leaning synthesis**.
- One-line description: Balanced and readable on the surface, yet still leans reject because strengths and weaknesses are not synthesized.

### System L · GPT-4o
- Strongest claim: strongest raw verdict accuracy on the nine-paper slice; strongest accepted-paper accuracy on the single-run 48-paper table above among configurations whose verdict inference is structurally reliable.
- Limitation: lower strict recall than the more exhaustive systems.
- Public framing: **selective and comparatively well calibrated**.
- One-line description: Selective, comparatively well calibrated, and the strongest raw verdict performer in the public named-paper slice.

### System M · GPT-4o
- Strongest claim: broad loose recall.
- Limitation: one false positive on the public rejected pair; attention can drift toward non-blocking issues. **All 48 System M reviews additionally contain multi-agent coordination artifacts (e.g., inter-agent messages, repeated draft fragments) that make verdict inference unreliable regardless of method.** The accepted-paper accuracy in the 48-paper table reflects our pipeline's interpretation; under alternative inference methods the figure ranges widely.
- Public framing: **broad coverage; verdict inference is unreliable for this configuration**.
- One-line description: Broad coverage of official concerns, but the system's verdict cannot be read reliably from its review text — concern-level metrics are the trustworthy surface here.

### System O · Opus
- Strongest claim: specific technical auditing, numerical checks, and line-level critique.
- Limitation: low alignment with official decision-driving concerns; highest phantom rate.
- Public framing: **technical auditor, weak decision alignment**.
- One-line description: Excellent at technical spot-checking, but often focused on a different stratum of concerns than what drove the decision.

## 5. Evaluation conditions

Keep a compact evaluation-conditions note attached anywhere this comparison appears.

### Minimal public wording

> Baselines were run through a released SDK adaptation layer on sanitized camera-ready PDFs with author and venue information removed. Results reflect these specific evaluation conditions and should be read as comparative diagnostics, not as definitive assessments of the native systems.

### Longer wording for README or appendix

- Prompts were loaded from the public baseline implementations where possible.
- API transport layers and PDF extraction differed from the original systems in documented ways.
- Some systems produce explicit scores; others require verdict inference from the review structure.
- Concern alignment evaluates the released outputs, not the underlying method in the abstract.
