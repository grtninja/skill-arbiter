# STARFRAME Operations Checklist

## Pre-Run

- Read `AGENTS.md`, `BOUNDARIES.md`, `HEARTBEAT.md`, and `INSTRUCTIONS.md`.
- Confirm whether changes touch one of: `starframe/`, `proxy/`, `tests/proxy`, `tests/starframe`, `configs/`, `metaranker/`.
- Capture touched endpoint contracts from diffs before editing.

## Proxy/Runtime Validation

- `POST`/call payload to `starframe/proxy/avatar.py` is valid and deterministic.
- Invalid intent payloads still enter fail-closed failure channel.
- Reflected `mx3_state` and quota values remain contract-compatible.
- Degraded-mode transitions include explicit and test-covered states.

## Endpoint Checks

- `GET /health`
- `GET /v1/unified/status`
- `POST /v1/unified/services/{service_name}/start|stop` (when touched)
- `GET /v1/unified/services`
- `GET /v1/shim/rag/status`

## Persona and Config Checks

- Persona pack discovery and registry changes preserve deterministic ID lookup.
- `configs/provider_config.schema.json` and related model examples remain loadable.
- Provider score/metrics changes keep fallback behavior explicit when service health is degraded.

## Regression Guards

- Update at least one focused regression test when changing:
  - proxy routing
  - health contract shape
  - scoring or degraded-mode policy
- Confirm docs sync if runtime surfaces are documented in `docs/` or `README.md`.
- If heartbeat lane is exercised and no issue is found, return exact success token: `HEARTBEAT_OK`.
