---
name: repo-b-mcp-comfy-bridge
description: Manage MCP adapter runtime and ComfyUI bridge integration in <PRIVATE_REPO_B>. Use when enabling MCP, updating adapter config, validating shim.comfy tools/resources, or troubleshooting MCP/Comfy availability and error contracts.
---

# REPO_B Shim MCP Comfy Bridge

Use this skill for MCP adapter and ComfyUI bridge operations.

## Workflow

1. Enable MCP with loopback-safe defaults.
2. Validate runtime status via REST endpoint.
3. Configure MCP runtime state with `/api/mcp/config` when needed.
4. Validate Comfy bridge resource/tool availability.

## Enable and Validate

```bash
export SHIM_ENABLE_MCP=1
export SHIM_MCP_HOST=127.0.0.1
export SHIM_MCP_PORT=9550
curl http://127.0.0.1:9000/api/mcp/status
```

Apply config:

```bash
curl -X POST http://127.0.0.1:9000/api/mcp/config \
  -H "content-type: application/json" \
  -d '{"enabled":true,"persist":true,"apply_now":true}'
```

## Comfy Bridge Controls

- `REPO_B_COMFYUI_ENABLED`
- `REPO_B_COMFYUI_BASE_URL`
- `REPO_B_COMFYUI_API_KEY`
- `REPO_B_COMFYUI_TIMEOUT_S`

## Reference

- `references/mcp-comfy-checklist.md`
