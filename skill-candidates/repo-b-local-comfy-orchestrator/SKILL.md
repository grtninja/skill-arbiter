---
name: repo-b-local-comfy-orchestrator
description: Compatibility wrapper for legacy local Comfy orchestration requests in <PRIVATE_REPO_B>. Route new MCP/Comfy operations to repo-b-mcp-comfy-bridge.
---

# REPO_B Local Comfy Orchestrator (Legacy Wrapper)

Use this wrapper to preserve legacy trigger compatibility.

For all new MCP/Comfy work, use `$repo-b-mcp-comfy-bridge`.

## Workflow

1. Detect legacy request intent (`local comfy orchestrator`, `comfy health check`, `shim.comfy` diagnostics).
2. Immediately route execution to `$repo-b-mcp-comfy-bridge`.
3. Keep loopback-only and fail-closed defaults unchanged.
4. Reuse legacy drop-in scripts only when older automation still calls them directly.

## Legacy Drop-In Hook Files (Still Supported)

These files remain available for backward-compatible automation:

- `assets/repo_b/tools/local_comfy_orchestrator.py` -> `tools/local_comfy_orchestrator.py`
- `assets/repo_b/tools/local_comfy_validate.py` -> `tools/local_comfy_validate.py`
- `assets/repo_b/tools/local_comfy_orchestrator.example.env` -> `tools/local_comfy_orchestrator.example.env`
- `assets/repo_b/tests/tools/test_local_comfy_orchestrator.py` -> `tests/tools/test_local_comfy_orchestrator.py`
- `assets/repo_b/tests/tools/test_local_comfy_validate.py` -> `tests/tools/test_local_comfy_validate.py`

## Legacy Environment (PowerShell)

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

## Legacy Run Command

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

- Canonical path: `$repo-b-mcp-comfy-bridge`
- `references/orchestrator-workflow.md`
- `references/validation-contract.md`
- `references/phase2-prompt-lifecycle-roadmap.md`
