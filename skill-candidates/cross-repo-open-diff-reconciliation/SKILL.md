---
name: "cross-repo-open-diff-reconciliation"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Review recent open diffs across multiple repos, classify repeated release/docs/tests gaps, and route each gap to the right remediation skill. Use when several repos are carrying unreleased work and you need a deterministic audit before patching or curating new skills."
---

# Cross-Repo Open Diff Reconciliation

Use this skill to turn recent multi-repo work into a bounded remediation map.

## Workflow

1. Route the request through `$skill-hub`.
2. Run `$skills-cross-repo-radar` with a bounded lookback window.
3. Inspect open diffs and changed-file clusters for:
   - release-hygiene misses
   - docs-lockstep drift
   - missing tests
   - policy/contract-sensitive changes
   - startup/runtime acceptance changes
4. Classify each repo finding into a small remediation lane.
5. Route findings to the most specific follow-on skill instead of patching blindly.
6. Produce a deterministic reconciliation table with:
   - repo
   - gap category
   - severity
   - evidence paths
   - suggested skill lane
7. When the user wants new skill curation, cluster repeated findings across repos and propose new skills or upgrades only after the reconciliation map is complete.

## Default Gap Routing

- `release_hygiene_missing` -> `$skill-arbiter-release-ops`
- `docs_lockstep_missing` -> `$docs-alignment-lock`
- `tests_missing` -> `$skill-common-sense-engineering`
- startup/launcher drift -> `$desktop-startup-acceptance`
- cross-repo contract/policy drift -> `$skill-enforcer`

## Required Evidence

- radar JSON output
- changed-file samples per repo
- category/severity counts
- remediation mapping for every flagged repo

## Scope Boundary

Use this skill for recent-work reconciliation and remediation routing.

Do not use it for:

1. deep runtime debugging after the gap is already classified
2. single-repo PR implementation when a more specific skill already fits
3. skill admission itself; use `$skill-auditor` and `$skill-arbiter-lockdown-admission` after curation

## References

- `references/finding-taxonomy.md`

## Loopback

If the reconciliation map is incomplete:

1. capture the missing repo or evidence slice
2. rerun the radar with narrowed scope or corrected repo list
3. continue only after every repo has a deterministic finding disposition
