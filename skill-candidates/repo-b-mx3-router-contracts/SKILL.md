---
name: repo-b-mx3-router-contracts
description: Validate MX3 shim model-router, ORT provider, and runtime packaging contracts. Use when changing route-mode derivation, router environment mapping, capability metadata, inference routing responses, exact ORT provider builds, or Electron/embedded-Node ABI ownership.
---

# Repo B MX3 Router Contracts

Use this skill for router-profile-aware model routing and ORT runtime-contract checks in the MX3 shim lane.

## Workflow

1. Read repository guardrails and routing docs before code changes.
2. Set router profile env vars for deterministic scenario testing:
   - `MX3_NETWORK_PROFILE`
   - `MESHGPT_ROUTER_MODE`
   - `ROUTER_NETWORK_MODE`
3. Run router-focused and ORT-contract tests after every behavior change.
4. Validate that health and inference responses expose effective routing and provider metadata.
5. Record profile-to-route evidence (`gaming`, `streaming`, `wfh`, `traditional_qos`, `ai_auto`).
6. Treat exact ORT package/build selection as part of the contract:
   - provider package version
   - CUDA vs DirectML lane
   - expected provider readiness and fail-closed behavior
   - Electron/embedded-Node ABI lane when desktop packaging changed

## Canonical Commands

Run from `<PRIVATE_REPO_B>` root:

```bash
python -m pytest tests/test_model_router_capabilities.py
python -m pytest inference/router/tests -k router
python -m pytest tests/test_inference_ort_runtime_contract.py
```

Profile smoke:

```bash
$env:MX3_NETWORK_PROFILE="gaming"
python -m pytest tests/test_model_router_capabilities.py -k route_mode
curl -s http://127.0.0.1:9010/v1/router/health
```

## Contract Requirements

- Router profile aliases must map deterministically to route mode.
- Capability metadata must include `network_profile`.
- Inference policy output must include active profile and effective policy.
- No silent fallbacks when profile env vars are explicitly set.
- ORT runtime metadata must expose the selected provider/build expectation and readiness state.
- Exact ORT package pins and provider assumptions must be documented when GPU/DirectML lanes change.
- Do not silently treat a missing expected provider as a successful fallback.

## Scope Boundary

Use this skill only for the `repo-b-mx3-router-contracts` lane and workflow defined in this file and its references.

Do not use this for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## Reference

- `references/router-contract-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture failing profile, route decision output, and test evidence.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
