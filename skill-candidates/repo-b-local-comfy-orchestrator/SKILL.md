---
name: repo-b-local-comfy-orchestrator
description: Run reliability-first local Comfy MCP resource orchestration in <PRIVATE_REPO_B> with strict validation, loopback-only policy, and fail-closed diagnostics.
---

# REPO_B Local Comfy Orchestrator

Use this skill to run manual local Comfy resource orchestration in <PRIVATE_REPO_B> through existing MCP contracts and emit validated diagnostics plus guidance hints.

## Workflow

1. Confirm loopback-safe MCP and fail-closed policy environment.
2. Probe MCP status from REST (`/api/mcp/status`).
3. Open JSON-RPC session to MCP adapter host/port.
4. Read required resources (`shim.comfy.status`, `shim.comfy.queue`, `shim.comfy.history`).
5. Validate all resource payloads with strict schema and freshness gates.
6. Emit deterministic diagnostics+hints JSON and stop on failures.

## Drop-In Hook Files

Copy these files into `<PRIVATE_REPO_B>` before first run:

- `assets/repo_b/tools/local_comfy_orchestrator.py` -> `tools/local_comfy_orchestrator.py`
- `assets/repo_b/tools/local_comfy_validate.py` -> `tools/local_comfy_validate.py`
- `assets/repo_b/tools/local_comfy_orchestrator.example.env` -> `tools/local_comfy_orchestrator.example.env`
- `assets/repo_b/tests/tools/test_local_comfy_orchestrator.py` -> `tests/tools/test_local_comfy_orchestrator.py`
- `assets/repo_b/tests/tools/test_local_comfy_validate.py` -> `tests/tools/test_local_comfy_validate.py`

## Required Environment (PowerShell)

```powershell
$env:REPO_B_LOCAL_COMFY_ORCH_ENABLED = "1"
$env:REPO_B_LOCAL_COMFY_ORCH_FAIL_CLOSED = "1"
$env:REPO_B_LOCAL_COMFY_ORCH_STATUS_MAX_AGE_SECONDS = "60"
$env:REPO_B_LOCAL_COMFY_ORCH_MAX_HINTS = "12"
$env:SHIM_ENABLE_MCP = "1"
$env:SHIM_MCP_HOST = "127.0.0.1"
$env:SHIM_MCP_PORT = "9550"
$env:SHIM_MCP_ALLOW_LAN = "0"
$env:MX3_COMFYUI_ENABLED = "1"
$env:MX3_COMFYUI_BASE_URL = "http://127.0.0.1:8188"
$env:MX3_COMFYUI_TIMEOUT_S = "10"
```

## Run Command

Run from `<PRIVATE_REPO_B>` root:

```bash
python tools/local_comfy_orchestrator.py \
  --task comfy-health-check \
  --json-out .codex/local_comfy/comfy-health-check.json \
  --repo-root .
```

## Usage Guardrails

Use real usage history before scale-up:

```bash
python3 "$CODEX_HOME/skills/usage-watcher/scripts/usage_guard.py" analyze \
  --input /path/to/usage.csv \
  --window-days 30 \
  --format table
```

```bash
python3 "$CODEX_HOME/skills/usage-watcher/scripts/usage_guard.py" plan \
  --monthly-budget <credits> \
  --reserve-percent 20 \
  --work-days-per-week 5 \
  --sessions-per-day 3 \
  --burst-multiplier 1.5 \
  --format table
```

## References

- `references/orchestrator-workflow.md`
- `references/validation-contract.md`
- `references/phase2-prompt-lifecycle-roadmap.md`
