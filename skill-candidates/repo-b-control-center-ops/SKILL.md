---
name: repo-b-control-center-ops
description: Operate and debug <PRIVATE_REPO_B> Control Center and thin-waist service surfaces. Use when working on connector routing, Lighthouse checks, MCP/Agent Bridge endpoints, pose bridge, or desktop startup/restart behavior.
---

# REPO_B Shim Control Center Ops

Use this skill for Control Center runtime and service-surface operations.

## Workflow

1. Start or restart using canonical headless path.
2. Validate API readiness and endpoint contracts.
3. Debug connector routing and diagnostics windows.
4. Keep no-flashing-console UX requirements intact.

## Canonical Operations

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restart_headless.ps1
```

```bash
curl http://127.0.0.1:9000/health
curl http://127.0.0.1:9000/v1/models
curl http://127.0.0.1:9000/api/resources
curl http://127.0.0.1:9000/api/mcp/status
curl http://127.0.0.1:9000/api/agent/capabilities
```

## Guardrails

- Do not introduce visible console windows for local desktop workflows.
- Keep routing and endpoint behavior backward-compatible.
- Keep REST and diagnostics surfaces loopback/local-first unless explicitly changed.

## References

- Endpoint checklist: `references/control-center-endpoints.md`
