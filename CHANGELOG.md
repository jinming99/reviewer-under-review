# Changelog

All notable changes to this project are documented here. This project follows [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-04 — Public benchmark and Named Papers release

### Added
- **48-paper calibration benchmark** with 864 pre-computed match graphs across six public baselines drawn from four published methods (Liang et al., Lu et al. AI Scientist, D'Arcy et al. MARG, OAR).
- **670 official concerns** extracted from OpenReview threads with severity, AC treatment, and decision-driver annotations; **79 decisive blockers** identified across the 48-paper set.
- **Named Papers public diagnostic slice**: nine end-to-end case studies (7 accepted, 2 rejected) with 54 released match graphs, 150 official concerns (102 resolved, 48 unresolved), and 7 decisive blockers. Raw PDFs and OpenReview threads linked for every paper.
- **Five-level evaluation ladder** (L0–L4) covering verdict accuracy, concern detection, verdict-stratified metrics, decision-aware metrics, and rebuttal-aware decomposition.
- **Standalone metric and audit scripts** under `scripts/` (alignment metrics, verdict-aware metrics, decisive-metric analysis, agentic extraction, lint, semantic audit).
- **Interactive static demo** at `demo/index.html` with progressive reveal, match graph explorer, named-paper case studies, and system diagnostic profiles.
- **Eight Claude Code skills** under `.claude/skills/` for running the full pipeline interactively (auto-discovered by Claude Code).
- **`RELEASE_MANIFEST.md`** describing the two-scope release contract (benchmark-wide vs Named Papers public slice).

### Scope
This release covers six public baselines on 48 calibration papers for benchmark-wide metrics, and nine named papers with linked raw artifacts for end-to-end inspection. See [RELEASE_MANIFEST.md](RELEASE_MANIFEST.md).

### Known limitations
- 48 papers is sufficient for qualitative patterns, not population-level estimates.
- Ground truth is the official review process, not absolute truth.
- Concern extraction and match graph construction use LLMs with independent verification; not fully automated.
- Verdict accuracy is method-sensitive for the four inferred-verdict configurations (both System A configurations emit native verdicts); concern-level diagnostics are method-stable. See the demo's Verdict Sensitivity panel and `data/audit/README.md`.

[0.1.0]: https://github.com/jinming99/reviewer-under-review/releases/tag/v0.1.0
