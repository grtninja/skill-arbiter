---
name: starframe-trace-ndjson-validate
description: Validate STARFRAME/GuardianTrace NDJSON packet integrity in PennyGPT-STARFRAME-Internal. Use when changing trace packet fields, guardian reroute behavior, or validation tooling that checks packet monotonicity and required envelope keys.
---

# STARFRAME Trace NDJSON Validate

Use this skill to protect packet stream contract integrity.

## Workflow

1. Generate or capture NDJSON packet streams.
2. Validate required packet fields and monotonic packet IDs.
3. Re-check guardian decision counters when reroute logic changes.

## Command

Run from `PennyGPT-STARFRAME-Internal` root:

```bash
python tools/trace_validate.py <path-to-ndjson>
```

## Required Fields

- `packet_id`
- `ts_unix_ms`
- `token_id`
- `emotion_ttl`
- `kv`
- `policy`
- `trust_anchor`

## Reference

- `references/trace-contract.md`
