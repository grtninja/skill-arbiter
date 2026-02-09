# Validation Contract

`tools/local_comfy_validate.py` enforces strict gates for Comfy MCP resources before orchestrator output can be treated as valid.

## Inputs

- `shim.comfy.status` payload
- `shim.comfy.queue` payload
- `shim.comfy.history` payload
- `status_max_age_seconds` (default `60`)
- `max_hints` (default `12`)

## Pass Requirements

Validation passes only when all checks pass:

1. `shim.comfy.status` payload is an object with:
   - `enabled=true`
   - `reachable=true`
   - empty `last_error`
   - parseable `checked_at` fresh within `status_max_age_seconds`
2. `shim.comfy.queue` payload is an object with:
   - list `running_prompt_ids`
   - list `pending_prompt_ids`
   - integer `running_count` matching running list length
   - integer `pending_count` matching pending list length
3. `shim.comfy.history` payload is an object with:
   - list `entries`
   - integer `count` matching entry list length
   - each entry containing typed fields (`prompt_id`, `queue_state`, `has_outputs`, `node_count`)

## Failure Behavior

On failure:

- `status=validation_failed`
- `reason_codes` include one or more of:
  - `mcp_unavailable`
  - `comfy_disabled`
  - `comfy_unreachable`
  - `schema_invalid`
  - `stale_status`
  - `policy_violation`
- no provider fallback is attempted

## Guidance Hint Shape

Each `guidance_hints` item contains:

- `resource`
- `finding`
- `evidence`
- `confidence`
- `priority`

Hints are deterministically sorted and truncated to `max_hints`.
