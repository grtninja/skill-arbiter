---
name: usage-watcher
description: Reduce paid credit spend and rate-limit risk with deterministic usage analysis and budget guardrails. Use when planning high-volume agent work, reviewing recent burn, or setting lean/standard/surge operating caps.
---

# Usage Watcher

Use this skill to control usage cost and avoid rate-limit surprises.

## Workflow

1. Capture recent usage history to CSV/JSON.
2. Run `usage_guard.py analyze` to measure burn rate and risk status.
3. Run `usage_guard.py plan` to set practical daily/session caps.
4. Select and record a chain usage mode (`economy`, `standard`, `surge`) from the analysis and plan outputs.
5. Apply the recommendations before large agent workflows.

## Analyze Command

```bash
python3 "$CODEX_HOME/skills/usage-watcher/scripts/usage_guard.py" analyze \
  --input /path/to/usage.csv \
  --window-days 30 \
  --daily-budget 140 \
  --weekly-budget 900 \
  --credits-remaining 236 \
  --five-hour-limit-remaining 100 \
  --weekly-limit-remaining 0 \
  --json-out /tmp/usage-analysis.json \
  --format table
```

## Budget Plan Command

```bash
python3 "$CODEX_HOME/skills/usage-watcher/scripts/usage_guard.py" plan \
  --monthly-budget 2800 \
  --reserve-percent 20 \
  --work-days-per-week 5 \
  --sessions-per-day 3 \
  --burst-multiplier 1.5 \
  --json-out /tmp/usage-plan.json \
  --format table
```

## Mandatory Chain Gate

Before finalizing skill chains, provide:

- `usage_analysis_json=/tmp/usage-analysis.json`
- `usage_plan_json=/tmp/usage-plan.json`
- `usage_mode=<economy|standard|surge>`

If this evidence is missing, chain selection is incomplete and must fail closed.

## Guardrail Policy

- Economy mode for discovery and triage.
- Standard mode for normal implementation tasks.
- Surge mode only for urgent deadlines.
- Prefer bounded scripts and cached artifacts over repeated broad discovery.
## Scope Boundary

Use this skill only for the `usage-watcher` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## References

- `references/cost-control-playbook.md`
- `references/usage-csv-template.csv`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
