---
name: mx3-shim-thin-waist-routing
description: Validate and troubleshoot thin-waist REST routing in memryx-mx3-python-shim. Use when changing /v1 models/chat/vision routes, async job queue endpoints, connector routing policy, or bind/exposure behavior.
---

# MX3 Shim Thin-Waist Routing

Use this skill for REST route verification and routing policy integrity.

## Workflow

1. Confirm loopback bind and LAN guard defaults.
2. Validate OpenAI-compatible façade routes.
3. Validate native async job endpoints and queue state.
4. Confirm routing policy remains centralized in `ModelRouter`.

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
