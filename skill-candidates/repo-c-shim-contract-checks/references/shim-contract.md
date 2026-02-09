# Shim Contract Summary

Expected endpoint contract example:
- `GET /health` -> `{"ok": true}`
- `GET /telemetry` -> telemetry schema-compatible payload

Rules:
- Use mock shim fixtures in CI integration tests.
- Keep fail-closed behavior for telemetry-required features.
- Avoid silent fallbacks that hide unreachable shim conditions.
