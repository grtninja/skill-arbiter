---
name: skill-cold-start-warm-path-optimizer
description: Measure first-run versus warm-run skill performance and generate prewarm/auto-invoke policy plans. Use when cold starts inflate latency or trigger retry storms.
---

# Skill Cold-Start Warm-Path Optimizer

Use this skill to convert cold-start latency into deterministic warm-path planning.

## Workflow

1. Collect execution logs with timestamp, skill, duration, and optional cold/cache fields.
2. Run `warm_path_optimizer.py analyze` for cold vs warm metrics.
3. Generate a prewarm and auto-invoke policy with `warm_path_optimizer.py plan`.
4. Apply the plan before high-throughput sessions.

## Analyze

```bash
python3 "$CODEX_HOME/skills/skill-cold-start-warm-path-optimizer/scripts/warm_path_optimizer.py" analyze \
  --input /path/to/skill-latency.csv \
  --window-days 30 \
  --cold-penalty-min-ms 800 \
  --min-invocations 3 \
  --rare-skill-max-invocations 2 \
  --never-auto-penalty-ms 3000 \
  --json-out /tmp/cold-warm-analysis.json \
  --format table
```

## Build Plan

```bash
python3 "$CODEX_HOME/skills/skill-cold-start-warm-path-optimizer/scripts/warm_path_optimizer.py" plan \
  --analysis-json /tmp/cold-warm-analysis.json \
  --max-prewarm 10 \
  --json-out /tmp/cold-warm-plan.json \
  --format table
```

## References

- `references/optimizer-workflow.md`
- `references/latency-contract.md`
