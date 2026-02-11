---
name: skill-trust-ledger
description: Keep a local reliability ledger for skills using recorded outcomes and arbiter evidence. Use when deciding whether to trust, restrict, or block skills over time.
---

# Skill Trust Ledger

Use this skill to preserve operational memory and avoid repeating past failure patterns.

## Workflow

1. Record outcome events after meaningful runs.
2. Ingest `skill-arbiter` evidence JSON after admissions.
3. Generate periodic trust-tier reports.
4. Use tiers to guide invoke/disable policy.

## Record Event

```bash
python3 "$CODEX_HOME/skills/skill-trust-ledger/scripts/trust_ledger.py" \
  --ledger ~/.codex/skills/.trust-ledger.local.json \
  record \
  --skill repo-b-mcp-comfy-bridge \
  --event success \
  --source manual \
  --note "Pilot run clean"
```

## Ingest Arbiter Evidence

```bash
python3 "$CODEX_HOME/skills/skill-trust-ledger/scripts/trust_ledger.py" \
  --ledger ~/.codex/skills/.trust-ledger.local.json \
  ingest-arbiter \
  --input /tmp/repo-b-mcp-comfy-bridge-arbiter.json
```

## Report Tiers

```bash
python3 "$CODEX_HOME/skills/skill-trust-ledger/scripts/trust_ledger.py" \
  --ledger ~/.codex/skills/.trust-ledger.local.json \
  report \
  --window-days 90 \
  --min-events 2 \
  --json-out /tmp/skill-trust-report.json \
  --format table
```

## References

- `references/ledger-workflow.md`
- `references/scoring-contract.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
