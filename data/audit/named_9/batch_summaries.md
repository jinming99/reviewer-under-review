# Batch Summaries

## Batch 1
Batch 1 has 4 of 18 tone–gate divergences. No paper has all 6 systems agreeing on tone or gate; `artificial_hivemind` shows the widest gate spread (ACCEPT / AMBIGUOUS / REJECT), while `adversarial_dejavu` splits 3–3 on tone. All three System M reviews remain structurally unreliable. A notable pattern is that accepted papers like `adversarial_dejavu` and `artificial_hivemind` still attract strong gate-based rejects from Opus/O systems, while lighter GPT-4o reviews often sound more accepting or only ambiguous.

## Batch 2
Batch 2 has 5 of 18 tone–gate divergences, the highest of the three batches. `from_assistant_pentest` is the clearest calibration anchor: all 6 systems are gate-REJECT even though two reviews (`L_GPT4o` and `M_GPT4o`) sound accepting in tone. `collabllm` shows the widest gate spread (ACCEPT / AMBIGUOUS / REJECT), and `cmdp_meta_safe_rl` also splits between hard rejects and gate-ambiguous reviews. System M is structurally broken in all three papers again. A notable pattern is that missing baseline/context comparisons are what most often flip a superficially positive security-paper review into a gate reject.

## Batch 3
Batch 3 has only 2 of 18 tone–gate divergences, making it the most stable batch. No paper achieves all-6 agreement, but `rl_backtracking_feedback` concentrates both divergences and is the only batch-3 paper with ambiguous gate outcomes; the other two papers split more cleanly into accept-vs-reject camps by system. System M remains structurally unreliable in all three papers. A notable pattern is that `rl_reasoning_limits` and `from_capabilities_pentest` show the familiar divide where Opus/O reviews reject on depth and validity, while lighter GPT-4o reviews often accept when they do not surface those deeper flaws.
