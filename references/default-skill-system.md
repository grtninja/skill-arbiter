# Default Skill System

This document contains the baseline chain and mandatory gates for `skill-arbiter`.

## Baseline chain for new work

1. Route with `skill-hub`.
2. Apply `skill-common-sense-engineering`.
3. Run `usage-watcher` and `skill-cost-credit-governor` when the work is agent-heavy, long-running, or multi-lane.
4. Run `skills-cross-repo-radar` for recent-work evidence.
5. Run `skills-third-party-intake` when external catalogs or mirrors are involved.
6. Run NullClaw self-checks.
7. Run NullClaw inventory refresh.
8. Review Codex / VS Code / GitHub Copilot interop surfaces.
9. Review the legitimacy split for official, owned, review-needed, and hostile skills.
10. Audit changed skills with `skill-auditor`.
11. Run `skill-arbiter-lockdown-admission` where admission evidence is required.
12. Run `skill-enforcer` for cross-repo policy alignment.
13. Record workflow XP/level progress with `python scripts/skill_game.py ...`.

## Binding mode and subagent policy

1. The operator-selected mode is authoritative.
2. Healthy local OpenClaw-compatible subagents are the preferred lane for quick bounded tasks.
3. Cloud subagents must default to lower-reasoning, lower-cost sidecar work.
4. Premium reasoning should stay on the main lane unless the operator explicitly asks for a heavier cloud sidecar.
5. Fast mode is not part of the governed default path.

## Mandatory gates

1. Privacy/public-shape gate must pass.
2. Self-governance scan must pass or findings must be intentionally addressed.
3. Built-in baseline drift must be reviewed for inventory-affecting changes.
4. Codex / VS Code / GitHub Copilot instruction-surface drift must be reviewed for interop-affecting changes.
5. Third-party risk changes must update tracked threat/source references.
6. Generated catalog must be refreshed after inventory-affecting changes.
7. Generated vetting report must be refreshed after legitimacy or interop-affecting changes.

## Related docs

- `AGENTS.md`
- `BOUNDARIES.md`
- `README.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `SKILL.md`
- `references/skill-catalog.md`
- `references/skill-vetting-report.md`
- `references/usage-chaining-multitasking.md`
- `references/vscode-skill-handling.md`
