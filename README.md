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

## What it does

1. Clones a curated skills source repo.
2. Installs each candidate skill into a destination skills directory.
3. Samples `rg.exe` process count once per second.
4. Removes + blacklists skills that exceed guardrails.
5. Emits CSV summary output and optional JSON evidence.

## Quick start

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  doc screenshot security-best-practices security-threat-model playwright \
  --window 10 --threshold 3 --max-rg 6
```

Dry-run mode (no filesystem changes):

```bash
python3 scripts/arbitrate_skills.py doc screenshot --dry-run
```

## CLI reference

```text
usage: arbitrate_skills.py [-h] [--window WINDOW] [--threshold THRESHOLD]
                           [--max-rg MAX_RG] [--json-out JSON_OUT]
                           [--repo REPO] [--dest DEST] [--blacklist BLACKLIST]
                           [--dry-run]
                           skills [skills ...]
```

Key options:

- `skills`: Curated skill names to test.
- `--window`: Sampling window in seconds (default `10`).
- `--threshold`: Consecutive non-zero threshold (default `3`).
- `--max-rg`: Remove skill if any sample >= value (default `6`).
- `--json-out`: Optional machine-readable report path.
- `--dest`: Destination skills home (default `~/.codex/skills`).
- `--blacklist`: Blacklist filename under `--dest` (default `.blacklist.local`).
- `--dry-run`: Report actions without modifying files.

## Output contract

- Stdout CSV header:
  - `skill,installed,max_rg,persistent_nonzero,action,note`
- JSON report (`--json-out`) includes:
  - run metadata
  - per-skill arbitration results
  - final blacklist list

## Security notes

- The script does not require API keys.
- It executes subprocesses using argument arrays (no shell string interpolation).
- Blacklisting is local to the configured skills destination.

See `SECURITY.md` for vulnerability reporting guidance and `SECURITY-AUDIT.md` for pre-publication scan notes.

## Repository layout

- `SKILL.md`: Skill definition used by Codex.
- `scripts/arbitrate_skills.py`: Arbitration implementation.
- `agents/openai.yaml`: Agent metadata.
- `references/publish-notes.md`: Publish defaults and notes.

## License

MIT. See `LICENSE.txt`.

## Support

If this project is useful in your workflow, you can support development on Patreon:  
<https://www.patreon.com/cw/grtninja>

## Contribution Policy

This repository is primarily owner-maintained. Issues and discussions are welcome, but external pull requests may be declined.
