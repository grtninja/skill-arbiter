---
name: skill-arbiter
description: Public candidate skill for arbitrating Codex skill installs on Windows hosts. Use when you need to reintroduce skills one-by-one, detect which skill triggers persistent rg.exe/CPU churn, and automatically remove or blacklist offending skills with reproducible evidence.
---

# Skill Arbiter

The St. Peter of skills.

Author: Edward Silvia  
License: MIT

Use this skill to decide which skills get admitted and which get quarantined.

## Run

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  doc screenshot security-best-practices security-threat-model playwright \
  --window 10 --threshold 3 --max-rg 3
```

For personally-created skills:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  my-new-skill \
  --source-dir "$CODEX_HOME/skills" \
  --window 10 --threshold 3 --max-rg 3 \
  --promote-safe
```

## Behavior

1. Install each candidate skill one-by-one from curated source.
2. Sample `rg.exe` process count once per second.
3. Remove and blacklist offenders automatically.
4. Treat blacklisted skills as permanently denied and delete them if present.
5. Respect local whitelist entries in `<dest>/.whitelist.local` and skip arbitration for approved skills.
6. Respect local immutable entries in `<dest>/.immutable.local`; immutable skills are never removed/blacklisted.
7. Third-party (repo-based) skills are deny-by-default and deleted unless `--promote-safe` is used.
8. `--promote-safe` auto-adds passing skills to whitelist + immutable files.
9. Emit optional JSON evidence via `--json-out`.

## Safe Modes

- Use `--dry-run` to preview actions without modifying files.
- Use `--dest` to test in an isolated skills directory.
