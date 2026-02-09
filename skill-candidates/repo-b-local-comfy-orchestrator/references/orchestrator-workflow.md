# Local Comfy Orchestrator Workflow

Use this runbook after copying drop-in files into `<PRIVATE_REPO_B>`.

## 1) Preflight

1. Confirm MCP is enabled and loopback-bound:
   - `SHIM_ENABLE_MCP=1`
   - `SHIM_MCP_HOST=127.0.0.1`
   - `SHIM_MCP_ALLOW_LAN=0`
2. Confirm Comfy bridge is enabled:
   - `MX3_COMFYUI_ENABLED=1`
3. Confirm fail-closed mode:
   - `REPO_B_LOCAL_COMFY_ORCH_FAIL_CLOSED=1`

## 2) Runtime Readiness

Run quick readiness check from `<PRIVATE_REPO_B>`:

```bash
curl http://127.0.0.1:9000/api/mcp/status
```

Required status fields:

- `enabled=true`
- `running=true`
- `host` loopback
- additive `comfy` payload present

## 3) Execute Manual Task

```bash
python tools/local_comfy_orchestrator.py \
  --task comfy-health-check \
  --json-out .codex/local_comfy/comfy-health-check.json \
  --repo-root .
```

## 4) Exit Codes

- `0`: success with validated diagnostics+hints
- `10`: MCP unavailable
- `11`: resource unavailable
- `12`: validation failed
- `13`: policy violation

## 5) Output Contract

JSON artifact keys:

- `status`
- `task_id`
- `mcp_probe`
- `resource_probe`
- `validation`
- `guidance_hints`
- `timing_ms`
- `reason_codes`
- `cloud_fallback_count`

## 6) JSON-RPC Calls

The orchestrator uses existing MCP methods only:

1. `initialize`
2. `resources/list`
3. `resources/read` (`shim.comfy.status`)
4. `resources/read` (`shim.comfy.queue`)
5. `resources/read` (`shim.comfy.history`)

## 7) Cost Tracking

Before rollout and weekly thereafter:

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
