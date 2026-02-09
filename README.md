# skill-arbiter

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE.txt)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform: Windows-focused](https://img.shields.io/badge/platform-Windows--focused-informational)
[![Support on Patreon](https://img.shields.io/badge/Support-Patreon-ff424d?logo=patreon&logoColor=white)](https://www.patreon.com/cw/grtninja)

Admit or quarantine Codex skills by detecting persistent `rg.exe` churn and preventing CPU thrash on large Windows repos.

`skill-arbiter` is a small, MIT-licensed utility skill that installs candidate Codex skills one-by-one, watches `rg.exe` process behavior, and automatically removes + blacklists noisy offenders with reproducible evidence.

## Why this exists

Some skills can accidentally trigger runaway repository scans on Windows hosts. This can cause:

- Sustained high CPU usage
- Repeated `rg.exe` process storms
- Slow or unstable editor/agent behavior

`skill-arbiter` provides an admission gate so only safe skills stay installed.
Third-party candidates are deny-by-default: they must pass checks and be explicitly promoted.

## What it does

1. Clones a curated skills source repo.
2. Installs each candidate skill into a destination skills directory.
3. Samples `rg.exe` process count once per second.
4. Removes + blacklists skills that exceed guardrails.
5. Emits CSV summary output and optional JSON evidence.

For personal/local skills, it can also auto-promote safe skills into local whitelist + immutable files.

## Quick start

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  doc screenshot security-best-practices security-threat-model playwright \
  --window 10 --threshold 3 --max-rg 3
```

Dry-run mode (no filesystem changes):

```bash
python3 scripts/arbitrate_skills.py doc screenshot --dry-run
```

Personal skill promotion (test local skills, then whitelist + immutable if safe):

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  my-new-skill another-skill \
  --source-dir "$CODEX_HOME/skills" \
  --window 10 --threshold 3 --max-rg 3 \
  --promote-safe
```

Personal lockdown mode (local-only + immutable pinning):

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  my-new-skill another-skill \
  --source-dir "$CODEX_HOME/skills" \
  --window 10 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

## Requirements

- Python 3.10+
- Git
- Windows host with PowerShell (`powershell.exe`)
- `rg.exe` available on the host (the script monitors `rg` process churn)
- Local git hook path configured once per clone:

```bash
./scripts/install_local_hooks.sh
```

Dependency declarations:

- `pyproject.toml`: project metadata + Python version floor
- `requirements.txt`: explicitly documents zero external Python dependencies

## CLI reference

```text
usage: arbitrate_skills.py [-h] [--window WINDOW] [--threshold THRESHOLD]
                           [--max-rg MAX_RG] [--json-out JSON_OUT]
                           [--repo REPO] [--source-dir SOURCE_DIR]
                           [--dest DEST] [--blacklist BLACKLIST]
                           [--whitelist WHITELIST] [--immutable IMMUTABLE]
                           [--dry-run] [--promote-safe]
                           [--personal-lockdown]
                           skills [skills ...]
```

Key options:

- `skills`: Curated skill names to test. Empty names are rejected.
- `--window`: Sampling window in seconds (default `10`).
- `--threshold`: Consecutive non-zero threshold (default `3`).
- `--max-rg`: Remove skill if any sample >= value (default `3`, allowed range `1-3`).
- `--json-out`: Optional machine-readable report path.
- `--source-dir`: Optional local source dir; installs from `<source-dir>/<skill>` and skips repo clone.
- `--dest`: Destination skills home (default `~/.codex/skills`).
- `--blacklist`: Blacklist filename under `--dest` (default `.blacklist.local`).
- `--whitelist`: Whitelist filename under `--dest` (default `.whitelist.local`).
- `--immutable`: Immutable filename under `--dest` (default `.immutable.local`).
- `--dry-run`: Report actions without modifying files.
- `--promote-safe`: Add passing skills to both whitelist and immutable files.
- `--personal-lockdown`: Personal mode; requires `--source-dir`, forces local promotion to whitelist+immutable, and rejects symlinked control files.

Whitelist behavior:

- Add one skill name per line in `<dest>/.whitelist.local`.
- Whitelisted skills are kept and skip arbitration when they are not blacklisted.

Immutable behavior:

- Add one skill name per line in `<dest>/.immutable.local`.
- Immutable skills are never removed or blacklisted by this script.

Blacklist behavior:

- Blacklisted skills are permanently denied by this script.
- If a blacklisted skill is present under `<dest>`, it is deleted (not archived).

Third-party behavior:

- Third-party candidates (repo-based runs, without `--source-dir`) are deleted unless `--promote-safe` is set.
- To admit a third-party skill after it proves safe, run with `--promote-safe` so it is added to whitelist + immutable.

Personal-lockdown behavior:

- Requires `--source-dir` (local-only admission; no curated clone flow for that run).
- Forces promotion of passing skills to both whitelist and immutable files.
- Rejects symlinked blacklist/whitelist/immutable control files.

## Output contract

- Stdout CSV header:
  - `skill,installed,max_rg,persistent_nonzero,action,note`
- JSON report (`--json-out`) includes:
  - run metadata
  - per-skill arbitration results
  - final blacklist/whitelist/immutable lists

## Release workflow

- For release-impacting PRs (for example changes under `scripts/`, `SKILL.md`, or other non-doc files), run:

```bash
python3 scripts/prepare_release.py --part patch
```

- Then refine the generated `CHANGELOG.md` notes so they match the PR.
- CI enforces this on pull requests via `scripts/check_release_hygiene.py`.

## Privacy lock

This repository is public-shape only. Private repository identifiers and user-specific absolute paths are blocked.

- Local pre-commit gate:

```bash
python3 scripts/check_private_data_policy.py --staged
```

- CI gate:

```bash
python3 scripts/check_private_data_policy.py
```

Use placeholders in docs and skill candidates:

- `<PRIVATE_REPO_NAME>` (or numbered forms like `<PRIVATE_REPO_1>`, `<PRIVATE_REPO_2>`)
- `$CODEX_HOME/skills`
- `$env:USERPROFILE\\...` (PowerShell)

## Security notes

- The script does not require API keys.
- It executes subprocesses using argument arrays (no shell string interpolation).
- Blacklisting is local to the configured skills destination.
- Symlinked control files are rejected to prevent redirected writes.

See `SECURITY.md` for vulnerability reporting guidance and `SECURITY-AUDIT.md` for pre-publication scan notes.

## Repository layout

- `AGENTS.md`: Repository operating rules and guardrails.
- `CHANGELOG.md`: Release history.
- `SKILL.md`: Skill definition used by Codex.
- `scripts/arbitrate_skills.py`: Arbitration implementation.
- `scripts/prepare_release.py`: Release bump helper.
- `scripts/check_release_hygiene.py`: PR release gate.
- `scripts/check_private_data_policy.py`: Privacy and private-data policy gate.
- `scripts/install_local_hooks.sh`: One-time local git hook installer.
- `agents/openai.yaml`: Agent metadata.
- `references/publish-notes.md`: Publish defaults and notes.
- `references/recommended-skill-portfolio.md`: Baseline skill catalog and rollout guidance for other repos.

## Candidate Skill Sets

Recent additions under `skill-candidates/`:

- `safe-mass-index-core`: bounded metadata-only indexing and query scripts with no-`rg` indexing policy.
- `repo-b-mass-index-ops`: repo-b wrapper presets for service/connector-oriented queries.
- `repo-d-mass-index-ops`: repo-d wrapper presets for sandbox-style UI/package trees.
- `repo-c-mass-index-ops`: repo-c wrapper presets with default sharded indexing for very large repos.
- `usage-watcher`: usage analysis and budget planning for paid credit control and rate-limit guardrails.

## License

MIT. See `LICENSE.txt`.

## Support

If this project is useful in your workflow, you can support development on Patreon:  
<https://www.patreon.com/cw/grtninja>

## Contribution Policy

This repository is primarily owner-maintained. Issues and discussions are welcome, but external pull requests may be declined.

## Skill Level-Up Declaration

When a skill is newly created or improved, include this exact declaration in the response/update text:

```text
New Skill Unlocked: <SkillName>
<SkillName> Leveled up to <LevelNumber>
```
