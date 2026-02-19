# Control Center Endpoint Checklist

Primary checks:
- `GET /health`
- `GET /telemetry/report`
- `GET /v1/models`
- `GET /api/resources`
- `GET /api/mcp/status`
- `GET /api/agent/capabilities`
- `GET /pose` and `GET /pose/status` when Repo D pose bridge is in scope

Desktop checks:
- `apps/mx3-control-center/src` exposes one clear window lifecycle path into `telemetry`/`view` controls.
- `apps/mx3-control-center/web/electron/windowBounds.js` owns startup bounds parsing and restore behavior.
- `apps/mx3-control-center/web/electron/windowManager.js` owns persisted window state transitions.
- `GET /telemetry/report` reflects resize and telemetry events when window state changes.

Use Lighthouse-style readiness checks for latency and failure diagnostics.
