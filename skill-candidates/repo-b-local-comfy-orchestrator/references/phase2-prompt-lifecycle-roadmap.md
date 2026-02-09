# Phase 2 Prompt Lifecycle Roadmap

Phase 1 is resource diagnostics only. Phase 2 introduces controlled prompt lifecycle orchestration after stability gates are met.

## Phase 2 Entry Gates

All gates should hold for at least two weeks:

1. Phase-1 fail rate is stable and diagnosable.
2. Median orchestration runtime stays within the target SLO.
3. Reason-code distribution shows low schema and connectivity churn.
4. Budget trend meets reduction objectives versus baseline.

## Planned Additions

1. Add controlled orchestration for:
   - `shim.comfy.prompt.submit`
   - `shim.comfy.prompt.status`
   - `shim.comfy.prompt.cancel`
2. Keep loopback-only and fail-closed defaults.
3. Keep prompt payload validation deterministic.
4. Preserve strict JSON-RPC error contract mapping.

## Safety Requirements

1. Prompt submit must require a typed prompt object.
2. Prompt status/cancel must require non-empty `prompt_id`.
3. No automatic cross-provider fallback on prompt failures.
4. Add explicit rate/queue guards before submit bursts.

## Non-Goals

- Do not relax phase-1 validation strictness for convenience.
- Do not enable LAN exposure by default.
- Do not auto-run prompt lifecycle orchestration without manual trigger policy.
