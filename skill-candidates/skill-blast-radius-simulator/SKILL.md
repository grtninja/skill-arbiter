---
name: skill-blast-radius-simulator
description: Simulate pre-install/pre-enable skill impact and require acknowledgement when risk exceeds thresholds. Use when admitting new skills or evaluating potentially risky updates.
---

# Skill Blast-Radius Simulator

Use this skill to estimate operational risk before enabling or installing new skills.

## Workflow

1. Select candidate skills to evaluate.
2. Run static blast-radius simulation.
3. Compare against baseline scores when available.
4. Require explicit acknowledgement for high-risk or high-delta results.

## Simulate

```bash
python3 "$CODEX_HOME/skills/skill-blast-radius-simulator/scripts/blast_radius_sim.py" \
  --skills-root skill-candidates \
  --skill my-new-skill \
  --ack-threshold high \
  --json-out /tmp/blast-radius-report.json \
  --format table
```

Compare to a previous run:

```bash
python3 "$CODEX_HOME/skills/skill-blast-radius-simulator/scripts/blast_radius_sim.py" \
  --skills-root skill-candidates \
  --skill my-new-skill \
  --baseline-json /tmp/previous-blast-radius-report.json \
  --json-out /tmp/blast-radius-report.json
```

## References

- `references/simulation-workflow.md`
- `references/risk-heuristics.md`
