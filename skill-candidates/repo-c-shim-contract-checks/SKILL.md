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

## Reference

- `references/shim-contract.md`
