---
name: skill-arbiter-lockdown-admission
description: Install and admit-test local skills with strict personal policy in the skill-arbiter repo. Use when adding or updating personal skills, requiring local-only sources, immutable pinning, blacklist quarantine, and rg.exe churn evidence.
---

# Skill Arbiter Lockdown Admission

Use this skill to admit local skills safely.

## Workflow

1. Validate candidate skill folders and names.
2. Run arbitration in local-only lockdown mode.
3. Confirm pass/fail actions and persisted lists.
4. Keep only passing skills whitelisted and immutable.

## Canonical Command

```bash
python3 scripts/arbitrate_skills.py <skill> [<skill> ...] \
  --source-dir /path/to/local/skills \
  --dest /home/eddie/.codex/skills \
  --window 10 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/arbiter-report.json
```

## Evidence Requirements

- CSV result row for each skill.
- JSON report with `max_rg`, `persistent_nonzero`, `action`, and `note`.
- Updated `.whitelist.local` and `.immutable.local` entries for passing skills.

## Reference

- `references/admission-checklist.md`
