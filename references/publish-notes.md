# Publish Notes

- Skill name: `skill-arbiter`
- Role: admission/quarantine gate for skill installs.
- Author attribution: Edward Silvia.
- License: MIT.

Recommended defaults:

- `--window 10`
- `--threshold 3`
- `--max-rg 3`
- blacklisted skills stay restricted by default (unless `--retest-blacklisted`)
- reject empty skill task names

Outputs:

- CSV summary on stdout.
- Optional JSON report via `--json-out`.
- Persistent blacklist updates in `<dest>/.blacklist.local`.
