# Case Studies

Observational case studies derived from running six published baseline AI review systems on a nine-paper diagnostic set with known venue decisions.

## File organization

### Per-paper stories
Each file covers one paper, its official review record, and how the baselines handled it. Papers span accepted and rejected outcomes at top-tier ML and NLP venues.

- `R1_beyond_problem_solving.md`: a rejected paper where the official decision cites theoretical framing and evaluation rigor.
- `A1_adversarial_dejavu.md`: an accepted ICLR 2026 paper on jailbreak dictionary learning with 22 official concerns.
- `A2_rl_backtracking.md`: a borderline-accept NeurIPS 2025 poster on reinforcement learning with backtracking feedback.
- `R2_A4_pentest_pair.md`: a revision pair (rejected then accepted, with A4 subsequently accepted to EMNLP 2025 main) in LLM penetration testing, useful for tracking how concerns evolve between submissions; includes the concern-level delta from R2 to A4.
- `A5_cmdp_meta_safe_rl.md`: an ICLR 2023 spotlight on meta-safe reinforcement learning — the first provable CMDP-within-online framework for the setting — with official concerns emphasizing theory over experiments.
- `E1_collabllm.md`: ICML 2025 Outstanding Paper (Oral) on collaborative LLMs, illustrating how literature knowledge can shift baseline behavior.
- `E2_artificial_hivemind.md`: NeurIPS 2025 Best Paper (Datasets & Benchmarks track) on open-ended homogeneity, where most baselines produce a reject verdict.
- `E3_rl_reasoning_limits.md`: NeurIPS 2025 Best Paper Runner-up (Oral) on RL and reasoning limits, a negative-result contribution backed by broad evidence.

### Cross-baseline analysis
- `baselines_comparison.md`: cross-baseline analysis organized by the evaluation ladder (L0 through L4).

### Per-baseline profiles
Each file covers one baseline method across all nine papers with observed strengths, limitations, and a one-line summary.

- `baseline_ai_scientist_opus.md`
- `baseline_ai_scientist_gpt4o.md`
- `baseline_liang_opus.md`
- `baseline_liang_gpt4o.md`
- `baseline_oar_opus.md`
- `baseline_marg.md`

## Scope

Sample size is nine papers — sufficient for qualitative patterns, not for population-level estimates. Percentages are reported alongside raw counts.

> **Verdict-inference scope.** Both System A configurations emit a native ACCEPT/REJECT field; for the other four baselines, verdicts are inferred from the review text. A two-rater audit of all 54 reviews in this slice found that verdict-level numbers are method-sensitive but concern-level metrics (recall, FDR, decisive precision, phantom rates) are not. Per-paper audited verdict counts appear in each case study; the demo's Verdict Sensitivity panel has the full breakdown. System M reviews contain multi-agent coordination artifacts that make verdict inference unreliable for that configuration regardless of method.
