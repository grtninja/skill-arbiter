# Skill Usage, Chaining, and Multitasking Guide

This guide defines the current safe chaining model for `skill-arbiter` as a live NullClaw host security app.

## Standard host-security chain

Use this sequence for non-trivial skill governance work:

1. `skill-hub`
2. `skill-common-sense-engineering`
3. `skills-cross-repo-radar`
4. `skills-third-party-intake` when external catalogs are involved
5. NullClaw self-checks
6. NullClaw inventory refresh
7. `skill-auditor`
8. `skill-arbiter-lockdown-admission`
9. `skill-enforcer`

## OpenClaw / NullClaw cross-repo chain

Use this when recent work spans multiple repos and upstream agent-skill surfaces:

1. `skill-hub`
2. `skills-cross-repo-radar`
3. `skills-third-party-intake`
4. `skill-openclaw-nullclaw-integration`
5. `code-gap-sweeping`
6. NullClaw self-checks
7. NullClaw inventory refresh
8. `docs-alignment-lock`
9. `skill-auditor`
10. `skill-enforcer`

## Multitasking rule

Split independent lanes explicitly, then merge only after each lane returns evidence.

Common lanes:

1. runtime or API implementation
2. source discovery and risk review
3. docs and policy alignment
4. app bring-up / operator verification

Use `multitask-orchestrator` when available. If not, apply the same split/merge discipline manually.

## Evidence to keep

- privacy gate result
- self-governance result
- inventory refresh artifact
- supply-chain findings
- skill-auditor output
- recent-work radar artifact
- generated skill catalog refresh

## Guardrails

1. Do not disable built-ins to make overlays work.
2. Do not auto-install directly from unvetted third-party sources.
3. Do not run heavy inventory work as part of cold-start health polling.
4. Do not open an external browser as part of the app path.
5. Keep repo-tracked docs public-shape only.
