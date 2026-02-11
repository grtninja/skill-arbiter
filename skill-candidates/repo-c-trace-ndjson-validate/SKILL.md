---
name: repo-c-trace-ndjson-validate
description: Validate Repo C/repo_c_trace NDJSON packet integrity in <PRIVATE_REPO_C>. Use when changing trace packet fields, guardian reroute behavior, or validation tooling that checks packet monotonicity and required envelope keys.
---

# Repo C Trace NDJSON Validate

Use this skill to protect packet stream contract integrity.

## Workflow

1. Generate or capture NDJSON packet streams.
2. Validate required packet fields and monotonic packet IDs.
3. Re-check guardian decision counters when reroute logic changes.

## Command

Run from `<PRIVATE_REPO_C>` root:

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

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
