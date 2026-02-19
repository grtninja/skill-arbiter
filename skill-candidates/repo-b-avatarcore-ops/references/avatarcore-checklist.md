# AvatarCore Operations Checklist

## Pre-Run

- Confirm required config exists and loads via `avatarcore_proxy.config_loader`.
- Confirm `docs/AGENTS.md` requirements are still aligned with boundary rules.

## Runtime Smoke

- `GET /health` returns `status` and `providers`.
- `POST /v1/avatarcore/query` returns a payload matching `AvatarCoreResponse`.
- `POST /v1/avatarcore/tts` returns audio envelope metadata and 200 for non-error routes.
- `POST /v1/avatarcore/stt` handles upload+metadata contracts.

## Bridge Session Lifecycle

- Create session: `POST /v1/avatarcore/bridge/session`.
- Read session state: `GET /v1/avatarcore/bridge/{session_id}`.
- Send heartbeat: `POST /v1/avatarcore/bridge/{session_id}/heartbeat`.
- Close session: `DELETE /v1/avatarcore/bridge/{session_id}`.

## Regression Guards

- `AVATARCORE_CONFIG__PROVIDERS__LLM__ORDER__*` env override should reorder provider chain.
- Retry and fallback tests should remain covered in `avatarcore_proxy/tests`.
- Telemetry/metadata payloads remain sanitized (no raw provider internals).
