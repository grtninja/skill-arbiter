---
name: skill-cost-credit-governor
description: Govern per-skill credit and token spend with deterministic warn/throttle/disable actions. Use when usage spikes, agent chatter, or budget overruns must be detected and contained.
---

# Skill Cost Credit Governor

Use this skill to prevent silent spend escalation across multi-skill workflows.

## Workflow

1. Export invocation usage history (CSV/JSON) with timestamp, skill, token, runtime, and optional caller fields.
2. Run `skill_cost_governor.py analyze` for a rolling window.
3. Review anomaly evidence (`cost_spike`, `inefficient_loop`, `agent_chatter`, `runtime_p95_high`).
4. Derive explicit chain action (`allow`, `warn`, `throttle`, `disable`) from anomaly evidence.
5. Apply proposed `warn`/`throttle`/`disable` actions.
6. Persist analysis and policy artifacts for audits.

## Analyze Usage

```bash
python3 "$CODEX_HOME/skills/skill-cost-credit-governor/scripts/skill_cost_governor.py" analyze \
  --input /path/to/skill-usage.csv \
  --window-days 30 \
  --soft-daily-budget 120 \
  --hard-daily-budget 180 \
  --soft-window-budget 2800 \
  --hard-window-budget 3400 \
  --spike-multiplier 2.0 \
  --loop-threshold 6 \
  --chatter-threshold 20 \
  --json-out /tmp/skill-cost-analysis.json \
  --format table
```

## Extract/Enforce Actions

```bash
python3 "$CODEX_HOME/skills/skill-cost-credit-governor/scripts/skill_cost_governor.py" decide \
  --analysis-json /tmp/skill-cost-analysis.json \
  --json-out /tmp/skill-cost-policy.json \
  --format table
```

Use `--force-global-action throttle` or `--force-global-action disable` for emergency containment.

## Mandatory Chain Gate

Before finalizing skill chains, provide:

- `skill_cost_analysis_json=/tmp/skill-cost-analysis.json`
- `skill_cost_policy_json=/tmp/skill-cost-policy.json`
- `global_action=<allow|warn|throttle|disable>`

If this evidence is missing, chain selection is incomplete and must fail closed.

## Action Policy Mapping

Map analysis outcomes to deterministic action:

1. `allow`:
   - no anomaly above threshold,
   - budget posture healthy.
2. `warn`:
   - isolated `cost_spike` or mild `runtime_p95_high`,
   - no persistent loop/chatter pattern.
3. `throttle`:
   - repeated `cost_spike` and/or `inefficient_loop`,
   - sustained budget pressure in current window.
4. `disable`:
   - severe or recurring `agent_chatter`/loop amplification,
   - hard-budget breach or high-confidence runaway behavior.

Record both `global_action` and per-skill actions in the policy artifact.
## Scope Boundary

Use this skill only for the `skill-cost-credit-governor` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## References

- `references/governor-workflow.md`
- `references/policy-contract.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
