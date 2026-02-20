# Default Skill System

This document contains the full baseline skill chain and mandatory skill-change gates referenced from `README.md`.

## Baseline chain for new work

1. Route requests with `skill-hub`.
2. Apply baseline sanity/hygiene checks with `skill-common-sense-engineering`.
3. Run `usage-watcher` to set usage mode (`economy`, `standard`, or `surge`) and capture usage analysis/plan JSON artifacts.
4. Run `skill-cost-credit-governor` to evaluate per-skill spend/chatter risk and capture analysis/policy JSON artifacts.
5. Run `skill-cold-start-warm-path-optimizer` to evaluate cold/warm latency and capture analysis/plan JSON artifacts.
6. For multi-repo work, run `code-gap-sweeping` to detect deterministic implementation gaps before mutation-heavy lanes.
7. For interrupted tasks, run `request-loopback-resume` to checkpoint lane state and produce deterministic next actions.
8. Run `skill-installer-plus` to plan installs/admissions and keep recommendation history current.
9. Audit new/changed skills with `skill-auditor`.
10. For cross-repo work, run `skill-enforcer` to enforce policy alignment.
11. For independent lanes, run `multitask-orchestrator`; reroute unresolved lanes through `skill-hub` loopback.
12. Record workflow XP/level progress with `python3 scripts/skill_game.py ...` using evidence JSON paths.

## Mandatory gates for new or updated skills

1. `skill-auditor` classification must be explicit: `unique` or `upgrade`.
2. `skill-arbiter-lockdown-admission` evidence must show a passable result (`action`, `persistent_nonzero`, `max_rg` captured).
3. If classification is `upgrade`, update existing skill boundaries before adding a duplicate candidate unless boundaries are explicitly distinct.
4. `skill-installer-plus` plan/admit outputs should be captured so recommendation quality improves over time.
5. Chaining decisions must include usage guardrail evidence from `usage-watcher`, `skill-cost-credit-governor`, and `skill-cold-start-warm-path-optimizer`.

## Related docs

- `AGENTS.md`
- `CONTRIBUTING.md`
- `SKILL.md`
- `.github/pull_request_template.md`
