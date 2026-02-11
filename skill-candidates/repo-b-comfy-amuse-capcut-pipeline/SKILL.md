---
name: repo-b-comfy-amuse-capcut-pipeline
description: Operate profile-driven ComfyUI pipelines with optional AMUSE enhancement and CapCut export guidance in <PRIVATE_REPO_B>. Use when validating /api/comfy/pipelines/*, /api/amuse/*, or CapCut handoff metadata.
---

# REPO_B Comfy AMUSE CapCut Pipeline

Use this skill for end-to-end media-pipeline operations that go beyond basic MCP/Comfy health checks.

## Workflow

1. Validate MCP and Comfy pipeline readiness on loopback.
2. Validate required pipeline profiles and CapCut export metadata contract.
3. Validate optional AMUSE stage status/capabilities when enabled.
4. Run one profile-driven pipeline request and verify deterministic response shape.

## Scope Boundary

Use this skill for `/api/comfy/pipelines/*`, `/api/comfy/workflows/*`, `/api/amuse/*`, and CapCut export guidance payload verification.

Do not use this skill for:

1. Generic MCP adapter enable/disable operations only (use `repo-b-mcp-comfy-bridge`).
2. Agent Bridge task safety or write-mode gates (use `repo-b-agent-bridge-safety`).
3. Windows-host vs WSL service topology diagnosis (use `repo-b-wsl-hybrid-ops`).

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
```

## Deterministic Preflight

```bash
python3 "$CODEX_HOME/skills/repo-b-comfy-amuse-capcut-pipeline/scripts/comfy_media_pipeline_check.py" \
  --base-url http://127.0.0.1:9000 \
  --require-profile small_video_capcut \
  --require-profile quality_video_capcut \
  --require-capcut \
  --require-amuse \
  --json-out /tmp/repo-b-comfy-media-preflight.json
```

## Runtime Checks

```bash
curl http://127.0.0.1:9000/api/comfy/pipelines/profiles
curl http://127.0.0.1:9000/api/comfy/workflows/templates
curl http://127.0.0.1:9000/api/amuse/status
curl http://127.0.0.1:9000/api/amuse/capabilities
```

Pipeline run example:

```bash
curl -X POST http://127.0.0.1:9000/api/comfy/pipelines/run \
  -H "content-type: application/json" \
  -d '{"profile":"small_video_capcut","wait_for_state":"RUNNING","capcut_preset":true}'
```

Expected response contract:

1. Top-level `profile`, `submit`, `status`, `wait_for_state`.
2. `capcut_export` present when `capcut_preset=true`.
3. `amuse` present when `amuse_enhance=true`.

## References

- `references/pipeline-contract.md`
- `scripts/comfy_media_pipeline_check.py`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture API evidence and JSON artifacts.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
