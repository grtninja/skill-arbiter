---
name: starframe-shim-contract-checks
description: Enforce MX3 shim runtime contract expectations in <STARFRAME_REPO>. Use when changing shim-facing adapters, telemetry dependencies, integration tests, or fail-closed behavior tied to MX3_SIDECAR_URL and mock-shim fixtures.
---

# STARFRAME Shim Contract Checks

Use this skill for shim endpoint contract safety.

## Contract Requirements

- Runtime features requiring telemetry must fail closed when shim is unavailable.
- `MX3_SIDECAR_URL` config path remains explicit.
- CI-facing integration tests use mock shim fixtures, not real hardware.
- Do not mask core import failures with `pytest.importorskip()`.

## Validation Commands

Run from `<STARFRAME_REPO>` root:

```bash
ruff check .
pytest -q
```

For focused shim contract review:

```bash
rg -n "MX3_SIDECAR_URL|importorskip|requires_real_sidecar|/health|/telemetry" -S AGENTS.md tests src starframe guardiantrace metaranker
```

## Reference

- `references/shim-contract.md`
