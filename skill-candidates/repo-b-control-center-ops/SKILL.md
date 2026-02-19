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
4. Validate desktop/window lifecycle for local launcher variants and verify no duplicate bound/restore logic.
5. Keep no-flashing-console UX requirements intact.

## Scope Boundary

Use this skill for Control Center startup/restart behavior and service-surface readiness checks.

Do not use this skill for:

1. Windows-host vs WSL split diagnostics (use `repo-b-wsl-hybrid-ops`).
2. Strict real-hardware probe/root-cause lanes (use `repo-b-hardware-first`).
3. PR preflight and docs lockstep gates (use `repo-b-preflight-doc-sync`).

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

## References

- Endpoint checklist: `references/control-center-endpoints.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
