<!--
Thanks for contributing. Keep PRs small and focused — one change per PR
is easier to review and easier to revert if something turns out to be
wrong.
-->

## What

<!-- One-sentence description of the change. -->

## Why

<!-- The motivation. If there is a linked issue or discussion, reference
it here. If the change is driven by a case-study finding or a data audit,
name it. -->

## How it was tested

<!-- How you verified the change works. Examples:
- opened demo/index.html in Safari and clicked through every tab
- ran the relevant skill (e.g. skill-3-concern-match-graph) against
  a user_runs/ workspace and confirmed the output YAML validates
- re-ran scripts/lint_concern_alignment.py against the affected
  data/ subtree
-->

## Scope hygiene

<!-- Required check for any change that touches visible content.
Delete this section if the PR only touches infrastructure that never
renders publicly (CI config, tests, tooling scripts). -->

- [ ] Every visible number belongs cleanly to either the **48-paper benchmark** or the **9-paper Named Papers public slice**; no blended claims.
- [ ] No banned vocabulary introduced (`insider`, `external`, `regeneration pending`, `10 papers`, `panel_*`, `decide_first_*`, `df_*`, `hidden systems`).
- [ ] Case study or narrative copy still ties each claim to either an official score, an official concern sheet, a released verdict table, or a match graph.
