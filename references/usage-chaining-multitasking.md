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

## Cybertron fabric host ops chain

Use this when building or auditing Cybertron host readiness, repo parity, model placement, or VRM display contracts:

1. `skill-hub`
2. `skills-cross-repo-radar`
3. `skill-common-sense-engineering`
4. `multitask-orchestrator`
5. `cybertron-fabric-host-ops`
6. `skill-auditor`
7. `skill-arbiter-lockdown-admission`
8. `skill-enforcer`

## Multitasking rule

Split independent lanes explicitly, then merge only after each lane returns evidence.

Common lanes:

1. runtime or API implementation
2. source discovery and risk review
3. docs and policy alignment
4. app bring-up / operator verification

Use `multitask-orchestrator` when available. If not, apply the same split/merge discipline manually.

## Subagent routing policy

1. The user chooses the operating mode. Arbiter recommendations may inform the plan, but they must not silently switch the session away from the operator-selected mode.
2. Prefer healthy local OpenClaw-compatible agents for quick bounded subagent tasks.
3. Treat local and cloud subagents as one governed pool, but preserve premium reasoning budget by assigning cloud lanes to lower-reasoning sidecar work first.
4. Use heavier cloud reasoning only when the operator explicitly asks for it or a hard blocker justifies it.
5. Fast mode is not part of the default governed subagent workflow.

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
