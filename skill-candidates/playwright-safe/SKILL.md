---
name: playwright-safe
description: Run browser automation with Playwright using a no-assets, low-churn workflow. Use when you need navigation, form actions, extraction, or screenshots without installing icon/image assets that can trigger repeated rg.exe scans.
---

# Playwright Safe

Use this skill for Playwright browser work when host churn sensitivity matters.

## Workflow

1. Run preflight to enforce no-assets policy for this skill package.
2. Run browser tasks through Playwright CLI commands.
3. Store outputs in task folders, not in the skill folder.
4. Keep commands deterministic and short.

## Preflight

Run this before automation tasks:

```bash
python3 "$CODEX_HOME/skills/playwright-safe/scripts/playwright_safe_preflight.py" \
  --skill-root "$CODEX_HOME/skills/playwright-safe" \
  --json-out /tmp/playwright-safe-preflight.json
```

## Command Patterns

Check runtime:

```bash
playwright --version
```

Install browser dependencies if needed:

```bash
playwright install chromium
```

Run a script:

```bash
node /path/to/script.js
```

## Guardrails

1. Do not add `assets/` to this skill.
2. Do not add image/icon files (`*.png`, `*.svg`, `*.jpg`, `*.jpeg`, `*.gif`, `*.ico`) to this skill.
3. Keep outputs outside `$CODEX_HOME/skills/playwright-safe`.
4. If churn is observed, rerun preflight and remove added assets immediately.

## References

- `references/no-churn-rules.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
