# Control Center Endpoint Checklist

Primary checks:
- `GET /health`
- `GET /telemetry/report`
- `GET /v1/models`
- `GET /api/resources`
- `GET /api/mcp/status`
- `GET /api/agent/capabilities`
- `GET /pose` and `GET /pose/status` when Repo D pose bridge is in scope

Use Lighthouse-style readiness checks for latency and failure diagnostics.
