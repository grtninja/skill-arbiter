---
name: "skillhub-trend-radar"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Track SkillHub trend and topic drift, maintain a bounded rewrite watchlist, and surface emerging gaps worth turning into repo-owned skills. Use when the marketplace query set shows new families or when the current shortlist has gone stale."
---

# SkillHub Trend Radar

Use this skill for recurring SkillHub trend and topic monitoring inside `skill-arbiter`.

## Workflow

1. Query SkillHub with a bounded topic pack instead of one-off keywords.
2. Group repeated hits into practical families such as queue, trace, voice, catalog, or governance.
3. Separate marketplace popularity from repo usefulness.
4. Promote only the families that match current STARFRAME systems and recent work.
5. Hand off concrete rewrite targets to `$skills-discovery-curation`.

## Required Evidence

- the query pack used
- repeated marketplace families observed
- shortlisted rewrite targets
- note of any previously missing family that is now active

## Guardrails

- Do not treat trending as trust.
- Do not import third-party bodies directly from this lane.
- Keep the watchlist bounded and actionable.
- Fail closed if the trend signal does not map to a real local system need.

## Best-Fit Companion Skills

- `$skillhub-marketplace-sync`
- `$skills-discovery-curation`
- `$skills-third-party-intake`
- `$skill-auditor`

## Scope Boundary

Use this skill only for marketplace trend monitoring and rewrite watchlist curation.

For full artifact regeneration or source-ledger updates, route through `$skillhub-marketplace-sync`.
