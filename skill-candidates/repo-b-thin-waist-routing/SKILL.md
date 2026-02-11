---
name: repo-b-thin-waist-routing
description: Validate and troubleshoot thin-waist REST routing in <PRIVATE_REPO_B>. Use when changing /v1 models/chat/vision routes, async job queue endpoints, connector routing policy, or bind/exposure behavior.
---

# REPO_B Shim Thin-Waist Routing

Use this skill for REST route verification and routing policy integrity.

## Workflow

1. Confirm loopback bind and LAN guard defaults.
2. Validate OpenAI-compatible façade routes.
3. Validate native async job endpoints and queue state.
4. Confirm routing policy remains centralized in `ModelRouter`.

## Scope Boundary

Use this skill for `/v1/*` façade and `/api/jobs` thin-waist routing behavior.

Do not use this skill for:

1. MCP adapter and `shim.comfy.*` contract diagnostics (use `repo-b-mcp-comfy-bridge`).
2. Agent Bridge capability/task safety checks (use `repo-b-agent-bridge-safety`).
3. Windows-host vs WSL connectivity troubleshooting (use `repo-b-wsl-hybrid-ops`).

## Quick Verification

```bash
curl http://127.0.0.1:9000/v1/models
curl -X POST http://127.0.0.1:9000/v1/chat/completions -H "content-type: application/json" -d '{"model":"llama-3.2-1b-instruct","messages":[{"role":"user","content":"ping"}]}'
curl -X POST http://127.0.0.1:9000/v1/vision -H "content-type: application/json" -d '{"model":"radeon-qwen3-vl-2b","prompt":"describe","image_data_url":"data:image/png;base64,<BASE64_PAYLOAD>"}'
```

```bash
curl -X POST http://127.0.0.1:9000/api/jobs -H "content-type: application/json" -d '{"type":"chat","prompt":"ping"}'
curl http://127.0.0.1:9000/api/resources
```

## Key Env Vars

- `SHIM_BIND_HOST`, `SHIM_BIND_PORT`, `SHIM_ALLOW_LAN`
- `SHIM_MAX_CONCURRENCY`, `SHIM_JOB_QUEUE_MAX`, `SHIM_JOB_TIMEOUT_S`
- `SHIM_VISION_MAX_IMAGE_BYTES`

## Reference

- `references/thin-waist-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
