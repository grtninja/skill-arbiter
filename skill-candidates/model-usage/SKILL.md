---
name: model-usage
description: Summarize per-model usage cost from local CodexBar cost JSON. Use when you need current-model or all-model cost breakdowns for Codex or Claude usage.
---

# Model Usage

Use this skill to report model-level usage cost from local CodexBar data.

## Workflow

1. Load cost data from `codexbar cost --format json` or from a saved JSON file.
2. Choose `current` for the most recent model signal, or `all` for aggregate breakdown.
3. Emit text or JSON output for downstream planning docs.
4. Feed this output into `usage-watcher` and `skill-cost-credit-governor` when needed.

## Current Model Summary

```bash
python3 "$CODEX_HOME/skills/model-usage/scripts/model_usage.py" \
  --provider codex \
  --mode current
```

## Full Model Breakdown

```bash
python3 "$CODEX_HOME/skills/model-usage/scripts/model_usage.py" \
  --provider codex \
  --mode all \
  --format json \
  --pretty
```

## File/Stdin Input

```bash
python3 "$CODEX_HOME/skills/model-usage/scripts/model_usage.py" \
  --provider claude \
  --input /tmp/codexbar-cost.json \
  --mode all
```

## Guardrails

- Use local input only in this lane.
- Do not commit raw usage exports that include personal metadata.
- Keep derived summaries in JSON/text artifacts under `.tmp/` for reproducible review.

## Scope Boundary

Use this skill only for model-level usage summarization.

Do not use this skill for billing exports, payment actions, or account mutation.

## References

- `references/codexbar-cli.md`
