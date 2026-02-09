---
name: meshgpt-ddc-coordinator-smoke
description: Run and debug MeshGPT DDC node/coordinator smoke workflows. Use when changing coordinator endpoints, job fetch/submit flow, runtime registration, or backend dispatch paths that must be verified with local coordinator execution.
---

# MeshGPT DDC Coordinator Smoke

Use this skill for local coordinator+node runtime validation.

## Workflow

1. Launch local coordinator stub.
2. Start node runtime with verbose policy path.
3. Confirm one embeddings flow completes.
4. Verify telemetry emits expected lifecycle markers.

## Canonical Smoke Commands

Run from `<MESHGPT_REPO>` root:

```bash
uvicorn packages.coordinator.app.main:app --port 8787 --reload
```

In a second shell:

```bash
python -m meshgpt_node --policy config/device_policy.json --verbose
```

## Smoke Expectations

- Coordinator endpoints reachable: `/v1/register`, `/v1/fetch_job`, `/v1/submit`.
- Runtime registration succeeds.
- At least one job completes and telemetry includes `job.end`.
- Credit preview logs are emitted without payout actions.

## Reference

- `references/smoke-signals.md`
