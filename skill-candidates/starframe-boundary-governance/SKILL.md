---
name: starframe-boundary-governance
description: Keep PennyGPT-STARFRAME-Internal changes aligned with BOUNDARIES.md and AGENTS.md governance. Use when modifying trust-layer architecture, cross-repo interfaces, packaging docs, or any change that could blur cognitive vs hardware execution boundaries.
---

# STARFRAME Boundary Governance

Use this skill to keep architecture and governance constraints intact.

## Workflow

1. Read `BOUNDARIES.md` and `AGENTS.md` before coding.
2. Confirm changes stay in trust-layer lane (policy, scoring, telemetry libraries).
3. Reject coupling to hardware-execution internals from shim/DDC repos.
4. Run lint/tests and document governance impact in PR notes.

## Quick Governance Checks

```bash
rg -n "BOUNDARIES.md|MX3_SIDECAR_URL|Windows-SDK|fail-closed|trust-layer" -S README.md AGENTS.md docs src starframe guardiantrace metaranker
ruff check .
pytest -q
```

## Output Requirements

- Explicit statement of boundary-safe scope.
- Updated docs when contracts/interfaces shift.
- No new prohibited phrasing or dependency coupling.

## Reference

- `references/boundary-checks.md`
