# Publish Notes

- Skill name: `skill-arbiter`
- Role: admission/quarantine gate for skill installs.
- Author attribution: Edward Silvia.
- License: MIT.

Recommended defaults:

- `--window 10`
- `--threshold 3`
- `--max-rg 3`
- blacklisted skills are permanently denied and deleted if present
- local whitelist supports pre-approved skills (`<dest>/.whitelist.local`)
- local immutable list prevents removal/blacklisting (`<dest>/.immutable.local`)
- third-party candidates are deny-by-default unless `--promote-safe` is used
- personal lockdown mode (`--personal-lockdown`) requires `--source-dir`, auto-promotes safe skills, and rejects symlinked control files
- reject empty skill task names

Outputs:

- CSV summary on stdout.
- Optional JSON report via `--json-out`.
- Persistent blacklist updates in `<dest>/.blacklist.local`.
- Persistent whitelist/immutable updates when promoted.
