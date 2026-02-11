---
name: local-compute-usage
description: Enforce local-first Codex execution through VS Code workspace and connected local apps/services/hardware, with MemryX shim priority and fail-closed remote-host checks.
---

# Local Compute Usage

Use this skill when work must stay on local compute across service and hardware surfaces.

## Workflow

1. Run local preflight to validate workspace, VS Code CLI availability, endpoint host locality, and hardware readiness commands.
2. Pin runtime URLs and guardrail env vars to loopback/local values.
3. Route execution through existing local service and hardware skills (especially MemryX shim lanes).
4. Fail closed if non-local hosts or hardware-check failures are detected.

## Local Preflight

Run from the active workspace root:

```bash
python3 "$CODEX_HOME/skills/local-compute-usage/scripts/local_compute_preflight.py" \
  --workspace-root . \
  --require-vscode \
  --url http://127.0.0.1:9000/health \
  --url http://127.0.0.1:10000 \
  --probe-http \
  --strict-probe \
  --hardware-check "acclBench --hello" \
  --json-out /tmp/local-compute-preflight.json
```
For non-MemryX hardware lanes, replace `--hardware-check` with lane-appropriate local hardware commands.

## MemryX Shim-First Routing

When the user is actively working on MemryX shim flows:

1. Use `$repo-b-control-center-ops` for service startup/restart and endpoint readiness.
2. Use `$repo-b-hardware-first` for real-hardware diagnostics and deterministic probe evidence.
3. Use `$memryx-official-hardware-check` when official service checks fail (`127.0.0.1:10000` path).
4. Use `$repo-b-thin-waist-routing` and `$repo-b-mcp-comfy-bridge` for API/MCP routing diagnostics.
5. Use `$repo-b-local-bridge-orchestrator` for read-only bridge orchestration.

## Local Environment Defaults (PowerShell)

```powershell
$env:REPO_B_SIDECAR_URL = "http://127.0.0.1:9000"
$env:REPO_B_FORCE_LOCAL_ONLY = "1"
$env:REPO_B_CONTINUE_BRIDGE_ENABLED = "1"
$env:REPO_B_CONTINUE_MODE = "read_only"
$env:REPO_B_CONTINUE_ALLOWED_ROOTS = "$env:USERPROFILE\Documents\GitHub\<PRIVATE_REPO_B>"
```

## Guardrails

1. Do not route required service traffic to non-local hosts unless the user explicitly authorizes it.
2. Do not skip required hardware checks for hardware-backed workflows.
3. Prefer local scripts, local MCP adapters, local service endpoints, and local hardware probes over cloud-hosted alternatives.
4. Treat hostname drift or hardware-check failure as a policy violation and stop before mutation steps.

## Scope Boundary

Use this skill when the task is primarily about enforcing local compute usage policy and local service/hardware routing.

Do not use this skill for:

1. Deep repo-specific debugging that already has a dedicated skill lane.
2. Remote cluster/cloud execution plans.

For those lanes, route through `$skill-hub` and the most specific matching skill.

## References

- `references/local-first-checklist.md`
- `scripts/local_compute_preflight.py`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
