---
name: "repo-b-control-center-ops"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Operate and debug <PRIVATE_REPO_B> Control Center and thin-waist service surfaces. Use when working on connector routing, Lighthouse checks, MCP/Agent Bridge endpoints, pose bridge, canonical desktop startup/restart behavior, shortcut ownership, or window lifecycle/state ownership."
---

# REPO_B Shim Control Center Ops

Use this skill for Control Center runtime and service-surface operations.

## Workflow

1. Start or restart using the canonical repo-owned desktop path.
2. Close stale repo-owned windows/processes before relaunch.
3. Validate API readiness and endpoint contracts.
4. Debug connector routing, diagnostics windows, and startup state restore.
5. Validate desktop/window lifecycle ownership and verify no duplicate bounds/maximize/fullscreen ownership outside the window manager.
6. Enforce startup acceptance:
   - no visible empty console windows
   - no stale-window relaunches
   - frontend plus backend together
   - shortcuts/icons target the latest repo-owned launcher
7. Capture endpoint, window-manager, and launcher evidence for each restart fix.

## Scope Boundary

Use this skill for Control Center startup/restart behavior and service-surface readiness checks.

Do not use this skill for:

1. Windows-host vs WSL split diagnostics lane.
2. Strict real-hardware probe/root-cause lane.
3. PR preflight and docs lockstep gate lane.

## Canonical Operations

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Start-ControlCenter.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\stop.ps1
```

```bash
curl http://127.0.0.1:9000/health
curl http://127.0.0.1:9000/v1/models
curl http://127.0.0.1:9000/api/resources
curl http://127.0.0.1:9000/api/mcp/status
curl http://127.0.0.1:9000/api/agent/capabilities
```

## Desktop Window and Layout Checks

From `<PRIVATE_REPO_B>` root:

```bash
python -m pytest apps/mx3-control-center/tests
```

```bash
cd apps/mx3-control-center/web/electron
npm test -- windowBounds.test.js windowManager.test.js
```

From `<PRIVATE_REPO_B>/apps/mx3-control-center/web`:

```bash
npm run build
```

## Contract Guardrails

- Keep documented Control Center and startup diagnostics endpoints stable unless migration is approved.
- Keep connector routing and endpoint behavior backward-compatible.
- Preserve existing boundary for desktop window lifecycle: one authoritative window manager module, no duplicate bounds state ownership.
- Keep hidden/windowless launch limited to secondary helper processes, not the canonical desktop startup path.
- Treat Electron/embedded-Node ABI ownership and ORT provider readiness as part of the shipped startup contract when those lanes change.

## References

- Endpoint checklist: `references/control-center-endpoints.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
