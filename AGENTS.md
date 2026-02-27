# AGENTS.md

Repository rules for `skill-arbiter`. Follow these rules before opening a PR.

## 1) Core policy

- Treat this repository as public-shape only.
- Never commit private repo details, internal names, host-specific usernames, or absolute personal paths.
- Keep instructions generic and portable.
- Treat VS Code/Codex built-in skills as upstream baseline.
- Use this repository as an additive overlay and moderation layer only.
- Do not disable/replace built-ins to make overlay skills work.

Required placeholder style:

- Repo placeholders: `<PRIVATE_REPO_C>`, `<PRIVATE_REPO_B>`, `<PRIVATE_REPO_A>`, `<PRIVATE_REPO_D>`
- Skills root: `$CODEX_HOME/skills`
- PowerShell home paths: `$env:USERPROFILE\\...`

## 2) Hard privacy lock (must pass)

- Local pre-commit hook must be enabled:

```bash
./scripts/install_local_hooks.sh
```

- Commit gate (automatic via pre-commit):

```bash
python3 scripts/check_private_data_policy.py --staged
```

- CI gate (automatic on push/PR):

```bash
python3 scripts/check_private_data_policy.py
```

If either gate fails, do not proceed until violations are removed.

## 3) Release workflow (must pass for release-impacting changes)

For release-impacting changes (for example `scripts/`, `SKILL.md`, Python files, or non-doc behavior changes):

```bash
python3 scripts/prepare_release.py --part patch
```

Then update `CHANGELOG.md` notes to accurately match the PR.

PRs are checked by:

```bash
python3 scripts/check_release_hygiene.py
```

Docs-only/metadata-only changes (`README.md`, `references/`, `.github/`, etc.) may skip release bump.

## 4) Validation checklist before PR

Run from repo root:

```bash
python3 scripts/arbitrate_skills.py --help
python3 scripts/skill_game.py --help
python3 scripts/prepare_release.py --help
python3 scripts/check_release_hygiene.py --help
python3 scripts/check_private_data_policy.py
python3 -m py_compile scripts/arbitrate_skills.py scripts/skill_game.py scripts/prepare_release.py scripts/check_release_hygiene.py scripts/check_private_data_policy.py
```

## 5) Skill authoring rules

- Keep `SKILL.md` concise; move detailed material to `references/`.
- Prefer reusable scripts for fragile/repeated workflows.
- Do not hardcode private repo names or personal paths in candidate skills.
- Keep repo-specific candidate skills under `skill-candidates/` with placeholder naming.
- Keep overlay names distinct from VS Code built-ins unless intentionally extending existing upstream behavior.

When admitting local skills, prefer lockdown mode:

```bash
python3 scripts/arbitrate_skills.py <skill> --source-dir "$CODEX_HOME/skills" --personal-lockdown
```

Default skill system for new work:

1. Route with `skill-hub`.
2. Run baseline sanity/hygiene via `skill-common-sense-engineering`.
3. Run `usage-watcher` to set the active usage mode (`economy`, `standard`, or `surge`) and capture `usage-analysis` + `usage-plan` JSON artifacts.
4. Run `skill-cost-credit-governor` to evaluate per-skill spend/chatter risk and capture analysis/policy JSON artifacts.
5. Run `skill-cold-start-warm-path-optimizer` to evaluate prewarm policy and capture cold/warm analysis/plan JSON artifacts.
6. For multi-repo work, run `code-gap-sweeping` to detect deterministic implementation gaps.
7. For interrupted tasks, use `request-loopback-resume` to checkpoint lane state and produce deterministic next actions.
8. Use `skill-installer-plus` to plan skill installs/admissions and keep recommendation history current.
9. Audit new/changed skills with `skill-auditor`.
10. Enforce cross-repo policy alignment with `skill-enforcer` when working across repos.
11. For independent lanes, use `multitask-orchestrator`; reroute unresolved lanes through `skill-hub` loopback.
12. Record workflow XP/level progress with `python3 scripts/skill_game.py ...` using gate evidence JSON paths.

Mandatory skill-change gates:

1. Every new/updated skill must pass `skill-arbiter` admission and include evidence (`action`, `persistent_nonzero`, `max_rg`).
   Use `skill-arbiter-lockdown-admission` for this gate.
2. Every new/updated skill must be classified by `skill-auditor` as `unique` or `upgrade`.
3. If classification is `upgrade`, prefer updating existing skills instead of introducing duplicate candidates unless boundaries are explicitly documented.
4. Every new/updated skill should include `skill-installer-plus` evidence (`plan`/`admit` JSON paths and latest recommendation decision).
5. Every chain plan must include a usage guardrail decision with evidence paths from `usage-watcher`, `skill-cost-credit-governor`, and `skill-cold-start-warm-path-optimizer`; do not finalize chaining without these evaluations.

## 6) Security and mutation safety

- Do not commit secrets, tokens, credentials, or private keys.
- Preserve symlink safety controls and local-control-file protections in arbitration logic.
- Keep subprocess calls argument-safe (no shell interpolation).

## 7) Documentation alignment rule

When policy or workflow changes, update all relevant docs in the same PR:

- `AGENTS.md`
- `README.md`
- `CONTRIBUTING.md`
- `SKILL.md`
- `.github/pull_request_template.md`
- `references/skill-catalog.md`
- `references/usage-chaining-multitasking.md`
- `references/vscode-skill-handling.md`
- `references/skill-progression.md`

No PR should merge with contradictory instructions across these files.

## 8) Skill level-up declaration

When a skill is newly created or improved using this skillset, include this exact two-line declaration in the response:

```text
New Skill Unlocked: <SkillName>
<SkillName> Leveled up to <LevelNumber>
```

Use the real skill name for `<SkillName>`.  
Use a positive integer for `<LevelNumber>` (for example `1`, `12`, `99`).
