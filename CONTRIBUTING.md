# Contributing

## Development Setup

Requirements:

- Python 3.10+
- Git
- Windows host (for realistic `rg.exe` process sampling)

Quick checks:

```bash
python3 --version
./scripts/install_local_hooks.sh
python3 scripts/arbitrate_skills.py --help
python3 scripts/skill_game.py --help
python3 scripts/prepare_release.py --help
python3 scripts/check_release_hygiene.py --help
python3 scripts/check_private_data_policy.py
python3 -m py_compile scripts/arbitrate_skills.py scripts/skill_game.py scripts/prepare_release.py scripts/check_release_hygiene.py scripts/check_private_data_policy.py
```

## Release Procedure

For release-impacting changes (for example `scripts/`, `SKILL.md`, or non-doc files):

```bash
python3 scripts/prepare_release.py --part patch
```

Then update the generated `CHANGELOG.md` notes so they accurately describe the PR.

Docs-only and metadata-only PRs (for example `README.md`, `references/`, `.github/`) can skip the release bump.

For personal/local skill admission runs, prefer:

```bash
python3 scripts/arbitrate_skills.py <skill> --source-dir "$CODEX_HOME/skills" --personal-lockdown
```

For skill-centric workstreams, use the default system chain:

1. Route requests with `skill-hub`.
2. Apply baseline sanity checks with `skill-common-sense-engineering`.
3. Run `usage-watcher` to set usage mode and capture usage analysis/plan artifacts.
4. Run `skill-cost-credit-governor` to evaluate per-skill spend/chatter risk and capture analysis/policy artifacts.
5. Run `skill-cold-start-warm-path-optimizer` to evaluate cold/warm latency and capture analysis/plan artifacts.
6. For multi-repo workstreams, run `code-gap-sweeping` to detect deterministic implementation gaps first.
7. For interrupted workstreams, run `request-loopback-resume` to checkpoint lane state and compute deterministic next actions.
8. Run `skill-installer-plus` for install recommendations and admission ledger updates.
9. Audit new/changed skills with `skill-auditor`.
10. If multiple repos are involved, run `skill-enforcer` for policy alignment.
11. For independent subtasks, run `multitask-orchestrator` and loop unresolved lanes back through `skill-hub`.
12. Record XP/level updates with `python3 scripts/skill_game.py ...` after gate evidence is captured.

Mandatory checks for skill additions/updates:

1. `skill-auditor` output must classify each changed skill as `unique` or `upgrade`.
2. `skill-arbiter-lockdown-admission` evidence must be attached and pass review (`action`, `persistent_nonzero`, `max_rg`).
3. If classification is `upgrade`, prefer updating existing skills unless boundaries are explicitly distinct.
4. Include `skill-installer-plus` plan/admit evidence so recommendation history stays current.
5. Include usage guardrail evidence from `usage-watcher`, `skill-cost-credit-governor`, and `skill-cold-start-warm-path-optimizer` for chain decisions.

## Privacy Lock

This repository is public-shape only:

- Do not commit private repository identifiers.
- Do not commit user-specific absolute paths (for example `/home/<user>/...` or `C:\\Users\\<user>\\...`).
- Use placeholders in docs and skills (for example `<PRIVATE_REPO_C>`, `<PRIVATE_REPO_B>`, `<PRIVATE_REPO_A>`, `<PRIVATE_REPO_D>`, `$CODEX_HOME/skills`, `$env:USERPROFILE\\...`).

Hard gates:

- Pre-commit hook runs `python3 scripts/check_private_data_policy.py --staged`.
- CI runs `python3 scripts/check_private_data_policy.py` on all tracked files.

## Pull Requests

Before opening a PR:

1. Keep changes focused and scoped.
2. Update docs (`README.md`, `SKILL.md`, or `references/`) if behavior changes.
3. Run the quick checks above.
4. Ensure release metadata is updated for release-impacting changes (`pyproject.toml` + `CHANGELOG.md`).
5. Confirm CI `Release hygiene check` passes on the PR.
6. Confirm CI `Privacy policy check` passes on the PR.
7. Include rationale and risk notes in the PR description.

For new or updated skill candidates, include arbitration evidence summary in the PR:

1. Run `python3 scripts/arbitrate_skills.py <skill> [<skill> ...] --source-dir skill-candidates --window 10 --baseline-window 3 --threshold 3 --max-rg 3 --personal-lockdown --json-out /tmp/skill-arbiter-evidence.json`.
2. Report per-skill `action`, `persistent_nonzero`, and `max_rg`.
3. Run `python3 skill-candidates/skill-auditor/scripts/skill_audit.py --skills-root skill-candidates --include-skill <skill> --arbiter-report /tmp/skill-arbiter-evidence.json --require-arbiter-evidence`.
4. Report per-skill classification: `unique` or `upgrade` (with nearest peer).
5. Keep expected safe target: `action=kept`, `persistent_nonzero=false`, `max_rg=0`.
6. Record the run in the local game ledger:
   `python3 scripts/skill_game.py --task "<skill update>" --used-skill skill-hub --used-skill skill-common-sense-engineering --used-skill usage-watcher --used-skill skill-cost-credit-governor --used-skill skill-cold-start-warm-path-optimizer --used-skill skill-installer-plus --used-skill skill-auditor --used-skill skill-enforcer --used-skill skill-arbiter-lockdown-admission --arbiter-report /tmp/skill-arbiter-evidence.json --audit-report /tmp/skill-audit.json --enforcer-pass`.

If a skill was added or improved in the work, include this declaration in the response/update text:

```text
New Skill Unlocked: <SkillName>
<SkillName> Leveled up to <LevelNumber>
```

## Security

- Do not commit secrets, tokens, credentials, or private keys.
- If you identify a vulnerability, follow `SECURITY.md`.
