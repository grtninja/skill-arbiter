---
name: "skillhub-marketplace-sync"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Curate SkillHub marketplace discovery into repo-owned alignment artifacts, source reputation, and bounded promotion decisions. Use when SkillHub query sets, shortlist coverage, source ledgers, or alignment-matrix generation must be refreshed without promoting third-party skills past discovery-only by accident."
---

# SkillHub Marketplace Sync

Use this skill for the SkillHub marketplace-discovery lane in `skill-arbiter`.

## Workflow

1. Treat SkillHub as a marketplace source, not a trusted install source.
2. Refresh the bounded query set, shortlist evidence, and alignment artifacts together.
3. Keep these artifacts aligned in one pass:
   - `references/skillhub-source-ledger.*`
   - `references/skillhub-alignment-matrix.md`
   - `references/skill-catalog.md`
   - any generated evidence under `evidence/`
4. Recompute source posture and promotion limits from the refreshed first-wave results.
5. Fail closed if fetched metadata, GitHub source resolution, or intake evidence drifts.

## Required Evidence

- refreshed SkillHub alignment matrix
- refreshed SkillHub source ledger
- note of any new uncovered destination lanes
- explicit promotion decision after the refresh

## Guardrails

- Do not treat marketplace popularity as trust.
- Do not import upstream skill bodies directly in this lane.
- Keep `discovery_only` posture unless bounded intake evidence proves otherwise.
- Strip temporary fetch paths and private machine details from generated references.

## Best-Fit Companion Skills

- `$skills-third-party-intake`
- `$skills-discovery-curation`
- `$skill-auditor`
- `$docs-alignment-lock`

## Scope Boundary

Use this skill only for marketplace discovery sync, shortlist curation, and promotion-decision artifact refresh.

For repo-owned rewrites of uncovered destination lanes, route through `$skills-discovery-curation`.
