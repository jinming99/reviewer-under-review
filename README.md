<div align="center">

<br>

<img src="demo/brand/logo-light.svg#gh-light-mode-only" alt="Reviewer Under Review" width="120">
<img src="demo/brand/logo-dark.svg#gh-dark-mode-only" alt="Reviewer Under Review" width="120">

# Reviewer Under Review

*A benchmark and debugging harness for AI paper-review systems.*<br>
*Because someone has to grade the graders.*

<br>

[![Version](https://img.shields.io/badge/version-0.1.0-blue?style=flat-square)](CITATION.cff)
[![License](https://img.shields.io/badge/license-Apache_2.0-lightgrey?style=flat-square)](LICENSE)

<br>

[Scope](#scope) &middot; [Who this is for](#who-this-is-for) &middot; [Quick Start](#quick-start) &middot; [Evaluation Ladder](#the-evaluation-ladder) &middot; [Benchmark Data](#benchmark-data) &middot; [Limitations](#limitations) &middot; [Citation](#citation)

<br>

<img src="demo/pipeline-light.svg#gh-light-mode-only" alt="Pipeline: paper in, official and AI concerns out, bipartite match graph, five-level evaluation ladder." width="820">
<img src="demo/pipeline-dark.svg#gh-dark-mode-only" alt="Pipeline: paper in, official and AI concerns out, bipartite match graph, five-level evaluation ladder." width="820">

<br>

*The released benchmark spans 48 papers and 864 match graphs; the Named Papers section exposes nine end-to-end case studies with linked raw artifacts.*

---

</div>

<br>

## The Problem

Your AI reviewer got 50% accuracy. That could mean:

- it understood half the papers, or
- it rejected everything, or
- it found the right issues for the wrong reasons, or
- it invented concerns that don't exist.

Binary accuracy can't tell you which. This framework matches AI concerns to official reviewer concerns one by one, then scores each system on five diagnostic levels — each one surfacing a failure mode the level below hides.

<br>

## Who this is for

- **AI review system authors** — benchmark your system against six published baselines on the 48-paper calibration set.
- **AC / PC members evaluating AI review tools** — read nine end-to-end case studies where the venue decision is already known.
- **Meta-science researchers** — reuse 670 structured official-concern extractions and 864 match graphs as data on the shape of review disagreement.

<br>

## Scope

Two evidence layers — do not blend the counts.

- **48-paper benchmark** (24 accepted · 24 rejected) — the headline aggregate metrics. 864 match graphs, 670 official concerns, 79 decisive blockers, six baselines.
- **Named Papers public slice** (9 papers, 7 accepted · 2 rejected) — end-to-end case studies with linked PDFs and OpenReview threads. 54 match graphs, 150 official concerns, 7 decisive blockers.

Full contract in [RELEASE_MANIFEST.md](RELEASE_MANIFEST.md).

<br>

## Quick Start

Run the full concern-alignment pipeline on any paper in one prompt inside [Claude Code](https://claude.com/claude-code).

**1. Clone the repo and open Claude Code**

```bash
git clone https://github.com/jinming99/reviewer-under-review.git
cd reviewer-under-review && claude
```

**2. Drop your inputs into a workspace folder**

Create `user_runs/<paper_slug>/` with three files:

```
user_runs/<paper_slug>/
  paper.pdf              # the paper itself
  official_review.md     # the OpenReview reviews + meta-review
  ai_review.md           # your AI reviewer's output
```

**3. Paste this prompt into Claude Code**

```
Run the full concern-alignment pipeline on user_runs/<paper_slug>:
  1. Extract official concerns   (skill-1-official-concern-extraction)
  2. Extract agentic concerns    (skill-2-agentic-concern-extraction)
  3. Build the concern match graph (skill-3-concern-match-graph)
  4. Aggregate L0-L4 alignment metrics (skill-4-alignment-aggregate)

Write all artifacts under user_runs/<paper_slug>/out/ and give me
a one-page summary of the verdict comparison and concern-level
alignment.
```

Claude runs the four skills in sequence and produces the match graph plus metrics under your workspace. No CLI flags, no schema lookups &mdash; the skills handle both.

<br>

## The Evaluation Ladder

Each level reveals a failure mode invisible to the level below.

| Level | Question | What it catches |
|-------|----------|----------------|
| **L0** | Does it get accept/reject right? | Nothing useful. A system that rejects everything scores 50% on a balanced set. |
| **L1** | Does it find the real issues? | Phantoms: concerns raised by the AI with no grounding in the official review. |
| **L2** | Is accuracy balanced? | "50% accurate" can mean 0% on accepted papers (reject-everything behavior). |
| **L3** | When it says "fatal," is it right? | **False decisive rate**: how often the AI cries wolf on accepted papers. |
| **L4** | Does it focus on what the AC cared about? | Some systems catch resolved concerns but miss the actual blockers. |

Two systems can score identically at L0 while being completely different at L4. That is the point.

<br>

## Benchmark Data

864 match graphs across **six public baselines** drawn from four published methods, evaluated on a balanced 48-paper set (24 accepted, 24 rejected) from ICLR, NeurIPS, and ICML in the AI safety and alignment area:

| Baseline label | Method | Model |
|---|---|---|
| System L &middot; Opus | Single-prompt zero-shot ([Liang et al. 2024](https://www.nature.com/articles/s41562-024-02014-3)) | Claude Opus |
| System L &middot; GPT-4o | Single-prompt zero-shot ([Liang et al. 2024](https://www.nature.com/articles/s41562-024-02014-3)) | GPT-4o |
| System A &middot; Opus | Iterative reflection ([Lu et al. 2024](https://arxiv.org/abs/2408.06292)) | Claude Opus |
| System A &middot; GPT-4o | Iterative reflection ([Lu et al. 2024](https://arxiv.org/abs/2408.06292)) | GPT-4o |
| System M &middot; GPT-4o | Multi-agent swarm ([D'Arcy et al. 2024](https://arxiv.org/abs/2401.04259)) | GPT-4o |
| System O &middot; Opus | Progressive structured (OAR 2024) | Claude Opus |

**670** official concerns mapped. **170** resolved in rebuttal (40 with fixes absent from the reviewed PDF). **79** decisive blockers identified. Every match graph edge verified.

<br>

## Key Findings

- **Same accuracy, opposite pathology.** Two systems both score ~50% — one rejects nearly everything (98.6% / 2.8% rejected-vs-accepted accuracy), the other has a low-recall profile. Binary accuracy cannot distinguish them.
- **Model choice shifts outputs under fixed prompts.** Swapping Claude Opus for GPT-4o in System L swings accepted-paper accuracy by ~60 percentage points.
- **Phantoms are pervasive.** 38&ndash;78% of AI-generated concerns have no strict grounding in official reviews — some benign, some fabricated.

> **On verdict numbers.** Only both System A configurations emit a native ACCEPT/REJECT field; for the other four, verdicts are inferred from the review text. A two-rater audit of all 288 benchmark reviews confirms that *verdict*-level numbers are method-sensitive but *concern*-level diagnostics (recall, FDR, decisive precision, phantom rates) are not. See the demo's [Verdict Sensitivity](https://jinming99.github.io/reviewer-under-review/#audit) panel and Docs → Verdict Terminology page for the full explanation.

<br>

## Repo Structure

```
reviewer-under-review/
├── scripts/                    # Metrics, linting, audit
├── schemas/                    # YAML schemas for all data artifacts
├── data/
│   ├── official_concerns/      # 670 extracted official concerns
│   ├── agentic_concerns/       # ~1,000 extracted agentic concerns
│   ├── match_graphs/           # 864 bipartite alignments
│   └── ground_truth.yaml       # Paper metadata (venue, decision)
├── .claude/skills/             # 8 Claude Code skills (auto-discovered)
├── demo/                       # Interactive web demo (serve repo root over HTTP)
│   └── examples/               # Sample artifacts
└── docs/
    ├── case_studies/           # Per-paper narratives, baseline profiles
    └── *.md                    # Framework documentation
```

<br>

## Limitations

- **Sample size.** 48 papers is sufficient for demonstrating the framework and identifying replicated qualitative patterns. It is not sufficient for population-level estimates.
- **Ground truth is human review, not absolute truth.** Official reviewers disagree with each other. The framework measures alignment with the review process that produced the decision, not with some Platonic ideal of review quality.
- **LLM-in-the-loop.** Concern extraction and match graph construction use LLMs. Every edge is verified by an independent auditor (Skill 5b), but the pipeline is not fully automated end-to-end without human oversight.

<br>

## Citation

```bibtex
@inproceedings{jin2026concern,
  title={What Makes a Good AI Review? Concern-Level Diagnostics for AI Peer Review},
  author={Jin, Ming},
  year={2026},
  note={Under review}
}
```

See also [CITATION.cff](CITATION.cff) for structured citation metadata.

<br>

## License

Apache 2.0. See [LICENSE](LICENSE).
