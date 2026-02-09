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
python3 scripts/prepare_release.py --help
python3 scripts/check_release_hygiene.py --help
python3 scripts/check_private_data_policy.py
python3 -m py_compile scripts/arbitrate_skills.py scripts/prepare_release.py scripts/check_release_hygiene.py scripts/check_private_data_policy.py
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

If a skill was added or improved in the work, include this declaration in the response/update text:

```text
New Skill Unlocked
<Skill Name> leveled up to XX
```

## Security

- Do not commit secrets, tokens, credentials, or private keys.
- If you identify a vulnerability, follow `SECURITY.md`.
