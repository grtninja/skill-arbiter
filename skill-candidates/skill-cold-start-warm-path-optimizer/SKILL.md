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
4. Decide whether prewarm is required for this chain and record the decision.
5. Apply the plan before high-throughput sessions.

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

## Mandatory Chain Gate

Before finalizing skill chains, provide:

- `cold_warm_analysis_json=/tmp/cold-warm-analysis.json`
- `cold_warm_plan_json=/tmp/cold-warm-plan.json`
- `prewarm_required=<true|false>`

If this evidence is missing, chain selection is incomplete and must fail closed.

## Prewarm Decision Rubric

Set `prewarm_required` using deterministic thresholds:

1. `true` when:
   - cold penalty exceeds configured threshold, and
   - invocation frequency is above rare-skill threshold, and
   - lane is latency-sensitive for current task.
2. `false` when:
   - skill is rare in window, or
   - cold penalty is below threshold, or
   - lane is non-latency-critical.

Also record `never_auto_invoke` skills from the plan output to prevent hidden churn.
## Scope Boundary

Use this skill only for the `skill-cold-start-warm-path-optimizer` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## References

- `references/optimizer-workflow.md`
- `references/latency-contract.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
