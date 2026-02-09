---
name: meshgpt-ddc-telemetry-kv-guard
description: Protect MeshGPT DDC telemetry/privacy and encrypted KV pager contracts. Use when editing GuardianTrace adapters, STARFRAME policy gate logic, KV tiering/crypto code, or retention/privacy behavior tied to role acceptance.
---

# MeshGPT DDC Telemetry and KV Guard

Use this skill to keep telemetry and storage behavior safe and deterministic.

## Guardrails

1. Preserve append-only GuardianTrace NDJSON behavior.
2. Keep telemetry envelopes signed when configured.
3. Enforce STARFRAME privacy class and TTL gating at role entry.
4. Preserve encrypted KV paging behavior (AES-GCM + TTL enforcement).
5. Avoid storing raw prompts/responses or PII at rest.

## Validation Commands

Run from `<MESHGPT_REPO>` root:

```bash
ruff check .
pytest -q tests/telemetry tests/policy tests/test_guardiantrace_client.py
python -m meshgpt_node --policy config/device_policy.json --selftest config/mesh_ready_selftest.yaml
```

## Contract Targets

- KV API semantics stay stable:
  - `put(key: bytes, val: bytes, tier: str, ttl_s: int) -> None`
  - `get(key: bytes) -> Optional[bytes]`
- Telemetry events remain compact and append-only with rotation behavior intact.

## Reference

- `references/privacy-kv-checks.md`
