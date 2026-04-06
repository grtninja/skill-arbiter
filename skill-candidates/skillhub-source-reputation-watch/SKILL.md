---
name: skillhub-source-reputation-watch
description: Watch SkillHub source reputation over time by tracking fetch failures, review posture, security metadata, and promotion blockers across marketplace sources. Use when the repo needs a bounded reputation ledger instead of a one-shot snapshot.
---

# SkillHub Source Reputation Watch

Use this skill for long-lived source-reputation tracking of the SkillHub marketplace.

## Workflow

1. Track source posture at the repo and source level, not only per-skill names.
2. Record fetch failures, metadata mismatches, review status, and supply-chain blockers together.
3. Distinguish discovery-only sources from candidates that are becoming practically reusable.
4. Keep promotion decisions explicit and reversible.
5. Feed reputation changes back into marketplace sync and rewrite prioritization.

## Required Evidence

- current source posture
- repeated failure or mismatch notes
- promotion blockers or reputation gains
- explicit decision to keep, narrow, or promote the source

## Guardrails

- Do not promote a source on stars or downloads alone.
- Treat repeated fetch mismatch as a trust downgrade.
- Keep private machine details out of the ledger.
- Do not bypass third-party intake or lockdown admission.

## Best-Fit Companion Skills

- `$skillhub-marketplace-sync`
- `$skills-third-party-intake`
- `$skill-arbiter-lockdown-admission`
- `$docs-alignment-lock`

## Scope Boundary

Use this skill only for source-reputation and promotion-watch duties.

For creating repo-owned rewrite skills, route through `$skills-discovery-curation`.
