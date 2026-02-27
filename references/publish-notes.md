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
- additive overlay model on top of VS Code/Codex built-ins (no built-in replacement)

Operational references:

- `references/vscode-skill-handling.md` (built-in compatibility and reset recovery)
- `references/skill-catalog.md` (complete installed skill inventory)
- `references/usage-chaining-multitasking.md` (chain and lane execution guidance)
- `references/skill-progression.md` (core skill maturity levels and level-up rubric)

Outputs:

- CSV summary on stdout.
- Optional JSON report via `--json-out`.
- Persistent blacklist updates in `<dest>/.blacklist.local`.
- Persistent whitelist/immutable updates when promoted.

Export readiness notes for mass-index skill family:

- Core candidate: `safe-mass-index-core`
- Wrappers: `repo-b-mass-index-ops`, `repo-c-mass-index-ops`, `repo-d-mass-index-ops`
- Recommended admission command:

```bash
python3 scripts/arbitrate_skills.py \
  safe-mass-index-core repo-b-mass-index-ops repo-d-mass-index-ops repo-c-mass-index-ops \
  --source-dir skill-candidates \
  --window 10 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/mass-index-arbiter.json
```

- Export-ready acceptance target:
  - `action=kept`
  - `persistent_nonzero=false`
  - `max_rg=0` per skill

Export readiness notes for usage governance:

- Candidate skill: `usage-watcher`
- Recommended admission command:

```bash
python3 scripts/arbitrate_skills.py \
  usage-watcher \
  --source-dir skill-candidates \
  --window 10 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/usage-watcher-arbiter.json
```
