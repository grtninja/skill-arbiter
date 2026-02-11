---
name: repo-b-mcp-comfy-bridge
description: Canonical MCP adapter and Comfy bridge operations for <PRIVATE_REPO_B>. Use when enabling MCP, validating shim.comfy resources/tools, operating workflow/pipeline submissions, or running fail-closed Comfy diagnostics with optional AMUSE and CapCut contract checks. This is the primary replacement for repo-b-local-comfy-orchestrator.
---

# REPO_B Shim MCP Comfy Bridge

Use this skill as the canonical MCP + Comfy lane in `<PRIVATE_REPO_B>`.

`repo-b-local-comfy-orchestrator` is retained as a compatibility wrapper and should route here for new work.

## Workflow

1. Enforce loopback-only MCP and fail-closed defaults.
2. Validate MCP runtime state via `/api/mcp/status`.
3. Apply `/api/mcp/config` changes only when configuration drift is confirmed.
4. Validate required Comfy resources (`shim.comfy.status`, `shim.comfy.queue`, `shim.comfy.history`).
5. Validate Comfy tools (`shim.comfy.prompt.submit`, `shim.comfy.workflow.submit`, `shim.comfy.pipeline.run`).
6. Validate optional AMUSE status/capabilities and profile-level CapCut export metadata contracts.
7. Fail closed on stale status or schema contract violations.

## Scope Boundary

Use this skill for MCP adapter state/config plus `shim.comfy.*` resource health.

Do not use this skill for:

1. OpenAI-thin-waist chat/vision/jobs route debugging (use `repo-b-thin-waist-routing`).
2. Agent Bridge task/write-mode safety lanes (use `repo-b-agent-bridge-safety`).
3. Hybrid Windows-host/WSL network topology checks (use `repo-b-wsl-hybrid-ops`).

## Required Environment (PowerShell)

```powershell
$env:SHIM_ENABLE_MCP = "1"
$env:SHIM_MCP_HOST = "127.0.0.1"
$env:SHIM_MCP_PORT = "9550"
$env:SHIM_MCP_ALLOW_LAN = "0"
$env:MX3_COMFYUI_ENABLED = "1"
$env:MX3_COMFYUI_BASE_URL = "http://127.0.0.1:8188"
$env:MX3_COMFYUI_TIMEOUT_S = "10"
$env:MX3_COMFYUI_DEFAULT_WORKFLOW_PROFILE = "small_video"
$env:MX3_AMUSE_ENABLED = "1"
$env:MX3_AMUSE_BASE_URL = "http://127.0.0.1:3001"
$env:MX3_AMUSE_TIMEOUT_S = "15"
$env:REPO_B_LOCAL_COMFY_ORCH_FAIL_CLOSED = "1"
```

## Runtime/API Checks

```bash
curl http://127.0.0.1:9000/api/mcp/status
curl http://127.0.0.1:9000/api/comfy/workflows/templates
curl http://127.0.0.1:9000/api/comfy/pipelines/profiles
curl http://127.0.0.1:9000/api/amuse/status
curl http://127.0.0.1:9000/api/amuse/capabilities
```

Apply config:

```bash
curl -X POST http://127.0.0.1:9000/api/mcp/config \
  -H "content-type: application/json" \
  -d '{"enabled":true,"persist":true,"apply_now":true}'
```

## Resource Contract Checks

Validate these resource contracts before accepting diagnostics:

1. `shim.comfy.status`:
   - `enabled=true`
   - `reachable=true`
   - empty `last_error`
   - fresh `checked_at`
2. `shim.comfy.queue`:
   - `running_prompt_ids` and `pending_prompt_ids` lists
   - `running_count` and `pending_count` must match list lengths
3. `shim.comfy.history`:
   - `entries` list
   - `count` must match `entries` length

## Workflow/Pipeline Contract Checks

1. `shim.comfy.workflow.submit` accepts one of:
   - `workflow` object
   - `workflow_id`
   - `workflow_path`
   - `workflow_profile`
2. `shim.comfy.pipeline.run` supports profile defaults and optional AMUSE stage:
   - `profile` values include `small_video_capcut` and `quality_video_capcut`
   - `wait_for_state` must normalize to `NONE|QUEUED|RUNNING|DONE`
   - when `capcut_preset=true`, response includes `capcut_export.editor=capcut`
   - when `amuse_enhance=true`, response includes additive `amuse` payload

Pipeline run example:

```bash
curl -X POST http://127.0.0.1:9000/api/comfy/pipelines/run \
  -H "content-type: application/json" \
  -d '{"profile":"small_video_capcut","wait_for_state":"RUNNING","capcut_preset":true}'
```

## Advanced Diagnostics (Optional Legacy Tooling)

When deterministic artifact output is needed, use the legacy local orchestrator drop-ins from
`repo-b-local-comfy-orchestrator` (`tools/local_comfy_orchestrator.py`, `tools/local_comfy_validate.py`):

```bash
python tools/local_comfy_orchestrator.py \
  --task comfy-health-check \
  --json-out .codex/local_comfy/comfy-health-check.json \
  --repo-root .
```

## Comfy Bridge Control Vars

- `MX3_COMFYUI_ENABLED`
- `MX3_COMFYUI_BASE_URL`
- `MX3_COMFYUI_API_KEY`
- `MX3_COMFYUI_TIMEOUT_S`
- `MX3_COMFYUI_DEFAULT_WORKFLOW_PROFILE`
- `MX3_AMUSE_ENABLED`
- `MX3_AMUSE_BASE_URL`
- `MX3_AMUSE_TIMEOUT_S`

## References

- `references/mcp-comfy-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
