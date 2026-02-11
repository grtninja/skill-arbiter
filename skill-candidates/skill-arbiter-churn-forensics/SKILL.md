---
name: skill-arbiter-churn-forensics
description: Investigate rg.exe churn and quarantine decisions in skill-arbiter runs. Use when a skill causes CPU spikes, unexpected scans, blacklist actions, or when arbitration thresholds need evidence-backed tuning.
---

# Skill Arbiter Churn Forensics

Use this skill to diagnose and document churn incidents.

## Workflow

1. Re-run affected skills with JSON output enabled.
2. Compare `samples`, `max_rg`, and `persistent_nonzero` across candidates.
3. Classify outcomes as keep/delete with explicit rationale.
4. Persist a reproducible evidence trail for threshold adjustments.

## Diagnostic Run Example

```bash
python3 scripts/arbitrate_skills.py <skill> [<skill> ...] \
  --source-dir /path/to/local/skills \
  --dest $CODEX_HOME/skills \
  --window 10 --threshold 3 --max-rg 3 \
  --json-out /tmp/arbiter-forensics.json
```

## Forensics Notes

- `persistent_nonzero=true` indicates repeated rg activity streak.
- `max_rg >= max-rg threshold` triggers delete/blacklist action.
- Local immutable entries always win and prevent deletion.

## Reference

- `references/churn-signals.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
