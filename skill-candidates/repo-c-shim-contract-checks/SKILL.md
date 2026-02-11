---
name: repo-c-shim-contract-checks
description: Enforce REPO_B shim runtime contract expectations in <PRIVATE_REPO_C>. Use when changing shim-facing adapters, telemetry dependencies, integration tests, or fail-closed behavior tied to REPO_B_SIDECAR_URL and mock-shim fixtures.
---

# Repo C Shim Contract Checks

Use this skill for shim endpoint contract safety.

## Contract Requirements

- Runtime features requiring telemetry must fail closed when shim is unavailable.
- `REPO_B_SIDECAR_URL` config path remains explicit.
- CI-facing integration tests use mock shim fixtures, not real hardware.
- Do not mask core import failures with `pytest.importorskip()`.

## Validation Commands

Run from `<PRIVATE_REPO_C>` root:

```bash
ruff check .
pytest -q
```

For focused shim contract review:

```bash
rg -n "REPO_B_SIDECAR_URL|importorskip|requires_real_sidecar|/health|/telemetry" -S AGENTS.md tests src repo-c repo_c_trace ranking_engine
```
## Scope Boundary

Use this skill only for the `repo-c-shim-contract-checks` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## Reference

- `references/shim-contract.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
