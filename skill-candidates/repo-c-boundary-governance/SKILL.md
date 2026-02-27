---
name: repo-c-boundary-governance
description: Keep <PRIVATE_REPO_C> changes aligned with BOUNDARIES.md and AGENTS.md governance. Use when modifying trust-layer architecture, cross-repo interfaces, packaging docs, or any change that could blur cognitive vs hardware execution boundaries.
---

# Repo C Boundary Governance

Use this skill to keep architecture and governance constraints intact.

## Workflow

1. Read `BOUNDARIES.md` and `AGENTS.md` before coding.
2. Confirm changes stay in trust-layer lane (policy, scoring, telemetry libraries).
3. Reject coupling to hardware-execution internals from shim/DDC repos.
4. Run lint/tests and document governance impact in PR notes.

## Scope Boundary

Use this skill for architecture/governance boundary checks across docs, contracts, and cross-repo interfaces.

Do not use this skill for:

1. Policy file/schema validation execution lanes.
2. NDJSON trace packet validation mechanics.
3. Ranking engine scoring/report contract implementation details.

## Quick Governance Checks

```bash
rg -n "BOUNDARIES.md|REPO_B_SIDECAR_URL|Windows-SDK|fail-closed|trust-layer" -S README.md AGENTS.md docs src repo-c repo_c_trace ranking_engine
ruff check .
pytest -q
```

## Output Requirements

- Explicit statement of boundary-safe scope.
- Updated docs when contracts/interfaces shift.
- No new prohibited phrasing or dependency coupling.

## Reference

- `references/boundary-checks.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
