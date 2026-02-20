# skill-arbiter

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE.txt)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform: Windows-focused](https://img.shields.io/badge/platform-Windows--focused-informational)
[![Support on Patreon](https://img.shields.io/badge/Support-Patreon-ff424d?logo=patreon&logoColor=white)](https://www.patreon.com/cw/grtninja)

Admit or quarantine Codex skills by detecting persistent `rg.exe` churn and preventing CPU thrash on large Windows repos.

`skill-arbiter` is a small, MIT-licensed utility skill that installs candidate Codex skills one-by-one, watches `rg.exe` process behavior, and automatically removes + blacklists noisy offenders with reproducible evidence.

This repository is public-shape only: docs and skill candidates use placeholders (`<PRIVATE_REPO_C>`, `<PRIVATE_REPO_B>`, `<PRIVATE_REPO_A>`, `<PRIVATE_REPO_D>`, `$CODEX_HOME/skills`, `$env:USERPROFILE\\...`) instead of private identifiers and personal absolute paths.

## Table of Contents

- [Why this exists](#why-this-exists)
- [Key features](#key-features)
- [How it works](#how-it-works)
- [Quick start](#quick-start)
- [Installation](#installation)
- [Requirements](#requirements)
- [CLI reference](#cli-reference)
- [Output contract](#output-contract)
- [Advanced workflows](#advanced-workflows)
- [Security notes](#security-notes)
- [Repository layout](#repository-layout)
- [Candidate skill catalog](#candidate-skill-catalog)
- [License](#license)
- [Support](#support)
- [Contribution policy](#contribution-policy)
- [Skill level-up declaration](#skill-level-up-declaration)

## Why this exists

Some skills can accidentally trigger runaway repository scans on Windows hosts. This can cause:

- Sustained high CPU usage
- Repeated `rg.exe` process storms
- Slow or unstable editor/agent behavior

`skill-arbiter` provides an admission gate so only safe skills stay installed. Third-party candidates are deny-by-default: they must pass checks and be explicitly promoted.

## Key features

- Windows-first churn detection for `rg.exe` process storms
- Delta-over-baseline scoring to reduce false positives
- No external Python dependencies (`requirements.txt` is documentation-only)
- Local/personal admission modes with whitelist + immutable promotion
- Machine-readable evidence via CSV stdout and optional JSON reports
- Works with curated skill repos or local skill folders (`--source-dir`)

## How it works

Arbitration loop:

`clone/source -> baseline sample -> install one skill -> sample delta -> keep or quarantine -> emit evidence`

What the script does per skill:

1. Installs one candidate.
2. Measures baseline `rg.exe` count and post-install samples.
3. Scores churn using delta-over-baseline.
4. Keeps safe candidates or removes + blacklists offenders.
5. Writes CSV result rows and optional JSON run evidence.

## Quick start

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  doc screenshot security-best-practices security-threat-model playwright \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3
```

Dry-run mode (no filesystem changes):

```bash
python3 scripts/arbitrate_skills.py doc screenshot --dry-run
```

Personal lockdown mode (local-only + immutable pinning):

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  my-new-skill another-skill \
  --source-dir "$CODEX_HOME/skills" \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

## Installation

`skill-arbiter` is currently intended to run from a local clone.

```bash
git clone <repo-url>
cd skill-arbiter
./scripts/install_local_hooks.sh
python3 scripts/arbitrate_skills.py --help
```

If you already use Codex local skills, you can also run from:

- `$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py`

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
                           [--baseline-window BASELINE_WINDOW]
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
- `--baseline-window`: Baseline window in seconds before each install (default `3`).
- `--threshold`: Consecutive non-zero threshold (default `3`).
- `--max-rg`: Remove skill if any delta sample (`raw - baseline_max`) >= value (default `3`, allowed range `1-3`).
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
  - per-skill arbitration results (delta and raw sample fields)
  - final blacklist/whitelist/immutable lists

## Advanced workflows

### Default skill system

The full 12-step baseline chain and mandatory skill-change gates are documented in `references/default-skill-system.md`.

### Skill Game Loop

Use the local XP ledger to reward full workflow compliance:

```bash
python3 scripts/skill_game.py \
  --task "skill candidate update" \
  --used-skill skill-hub \
  --used-skill skill-common-sense-engineering \
  --used-skill usage-watcher \
  --used-skill skill-cost-credit-governor \
  --used-skill skill-cold-start-warm-path-optimizer \
  --used-skill skill-installer-plus \
  --used-skill skill-auditor \
  --used-skill skill-enforcer \
  --used-skill skill-arbiter-lockdown-admission \
  --arbiter-report /tmp/skill-arbiter-evidence.json \
  --audit-report /tmp/skill-audit.json \
  --enforcer-pass
```

Inspect current score/streak:

```bash
python3 scripts/skill_game.py --show
```

### Release workflow

For release-impacting PRs (for example changes under `scripts/`, `SKILL.md`, or other non-doc files), run:

```bash
python3 scripts/prepare_release.py --part patch
```

Then refine the generated `CHANGELOG.md` notes so they match the PR. CI enforces release hygiene with `python3 scripts/check_release_hygiene.py`.

### Privacy lock

This repository is public-shape only. Private repository identifiers and user-specific absolute paths are blocked.

Local pre-commit gate:

```bash
python3 scripts/check_private_data_policy.py --staged
```

CI gate:

```bash
python3 scripts/check_private_data_policy.py
```

## Security notes

- The script does not require API keys.
- It executes subprocesses using argument arrays (no shell string interpolation).
- Blacklisting is local to the configured skills destination.
- Symlinked control files are rejected to prevent redirected writes.

See `SECURITY.md` for vulnerability reporting guidance and `SECURITY-AUDIT.md` for pre-publication scan notes.

## Repository layout

- `AGENTS.md`: repository operating rules and guardrails
- `CHANGELOG.md`: release history
- `SKILL.md`: skill definition used by Codex
- `scripts/arbitrate_skills.py`: arbitration implementation
- `scripts/skill_game.py`: local XP/level scorer for workflow compliance
- `scripts/prepare_release.py`: release bump helper
- `scripts/check_release_hygiene.py`: PR release gate
- `scripts/check_private_data_policy.py`: privacy and private-data policy gate
- `scripts/install_local_hooks.sh`: one-time local git hook installer
- `agents/openai.yaml`: agent metadata
- `references/default-skill-system.md`: full default-chain and skill-change gate details
- `references/publish-notes.md`: publish defaults and notes
- `references/recommended-skill-portfolio.md`: baseline skill catalog and rollout guidance for other repos

## Candidate skill catalog

`skill-candidates/` is the full source of truth. The table below highlights representative skill groups.

| Skill name | Purpose | Type |
| --- | --- | --- |
| `safe-mass-index-core` | bounded metadata-only indexing with no-`rg` indexing policy | core |
| `usage-watcher` | usage analysis and budget planning for paid credit control | core |
| `skill-cost-credit-governor` | per-skill spend governance and warn/throttle/disable policy outputs | core |
| `skill-cold-start-warm-path-optimizer` | cold-vs-warm latency analysis and prewarm planning | core |
| `skill-installer-plus` | local-first install planning and admission recommendation loop | core |
| `code-gap-sweeping` | deterministic cross-repo implementation gap scans | core |
| `request-loopback-resume` | checkpoint/resume lane state for interrupted work | core |
| `repo-b-local-bridge-orchestrator` | read-only local Agent Bridge orchestration for `<PRIVATE_REPO_B>` | repo-specific |
| `repo-b-mcp-comfy-bridge` | canonical MCP adapter + Comfy bridge lane for `<PRIVATE_REPO_B>` | repo-specific |
| `repo-b-comfy-amuse-capcut-pipeline` | profile-driven Comfy pipeline with AMUSE + CapCut checks | repo-specific |
| `repo-c-mass-index-ops` | repo-c sharded indexing wrapper for very large trees | repo-specific |
| `repo-d-mass-index-ops` | repo-d indexing wrapper for sandbox-style UI/package trees | repo-specific |
| `skill-auditor` | audit and classify skills (`unique` vs `upgrade`) | meta-governance |
| `skill-enforcer` | enforce cross-repo policy alignment | meta-governance |
| `skill-hub` | route tasks to an ordered skill chain | meta-governance |

## License

MIT licensed. See `LICENSE.txt`.

## Support

If this project is useful in your workflow, you can support development on Patreon:  
<https://www.patreon.com/cw/grtninja>

## Contribution policy

This repository is primarily owner-maintained. Issues, discussions, and practical examples are welcome. External pull requests may be declined.

See `CONTRIBUTING.md` for development setup, validation checks, and release/privacy expectations.

## Skill level-up declaration

When a skill is newly created or improved, include this exact declaration in the response/update text:

```text
New Skill Unlocked: <SkillName>
<SkillName> Leveled up to <LevelNumber>
```
