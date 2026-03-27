# Contributing

## Development setup

Requirements:

- Python 3.10+
- Git
- Windows host
- `pywebview>=5.0` for the embedded desktop shell

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Quick validation:

```bash
./scripts/install_local_hooks.sh
python scripts/arbitrate_skills.py --help
python scripts/nullclaw_agent.py --help
python scripts/generate_skill_catalog.py
python scripts/generate_skillhub_alignment.py
python scripts/check_private_data_policy.py
python scripts/check_public_release.py
pytest -q
python -m py_compile scripts/arbitrate_skills.py scripts/check_private_data_policy.py scripts/check_public_release.py scripts/generate_skill_catalog.py scripts/nullclaw_agent.py scripts/nullclaw_desktop.py scripts/prepare_release.py scripts/check_release_hygiene.py skill_arbiter/about.py skill_arbiter/public_readiness.py
```

## Desktop app flow

Do not invert the startup model.

Required lifecycle:

1. app open
2. local agent attach/start
3. self-checks
4. inventory refresh
5. operator actions enabled

Do not add an external browser dependency to that flow.

For Windows-host launches, prefer the managed launcher:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_security_console.ps1
```

Install the branded desktop/start-menu shortcuts with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_security_console_shortcut.ps1
```

## Release procedure

For release-impacting changes:

```bash
python scripts/prepare_release.py --part patch
```

Then update `CHANGELOG.md` so it describes the shipped runtime and doc changes accurately.

## Privacy lock

This repository is public-shape only.

- Use placeholders for private repo names and user paths.
- Keep raw host evidence in ignored local state only.
- Do not commit usernames, absolute private paths, or private repo identifiers.

Required gates:

```bash
python scripts/check_private_data_policy.py --staged
python scripts/check_private_data_policy.py
python scripts/check_public_release.py
```

## Pull requests

Before opening a PR:

1. Keep runtime, tests, docs, and generated references aligned.
2. Run the validation block above.
3. Regenerate `references/skill-catalog.md`.
4. Update scope docs and policy docs if behavior changed.
5. Update release metadata for release-impacting changes.
6. Include risk notes for:
   - quarantine behavior
   - source trust changes
   - local advisor behavior
   - loopback API changes
   - public-release readiness changes
   - public-shape or maintainer-attribution changes
7. Keep built-ins additive; do not disable upstream VS Code/Codex skills.

## Skills and sources

For new or changed skill governance surfaces:

- run the supply-chain checks
- keep `references/third-party-skill-attribution.md` aligned
- keep `references/OPENCLAW_NULLCLAW_THREAT_MATRIX_2026-03-11.md` aligned when source risk posture changes
- keep `references/vscode-skill-handling.md` aligned when baseline or overlay handling changes
- keep `references/skillhub-alignment-matrix.md` and `references/skillhub-source-ledger.md` aligned when SkillHub intake posture changes

## Security

If you identify a security issue, follow `SECURITY.md`.
