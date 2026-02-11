---
name: repo-a-coordinator-smoke
description: Run and debug Repo A DDC node/coordinator smoke workflows. Use when changing coordinator endpoints, job fetch/submit flow, runtime registration, or backend dispatch paths that must be verified with local coordinator execution.
---

# Repo A DDC Coordinator Smoke

Use this skill for local coordinator+node runtime validation.

## Workflow

1. Launch local coordinator stub.
2. Start node runtime with verbose policy path.
3. Confirm one embeddings flow completes.
4. Verify telemetry emits expected lifecycle markers.

## Canonical Smoke Commands

Run from `<PRIVATE_REPO_A>` root:

```bash
uvicorn packages.coordinator.app.main:app --port 8787 --reload
```

In a second shell:

```bash
python -m repo_a_node --policy config/device_policy.json --verbose
```

## Smoke Expectations

- Coordinator endpoints reachable: `/v1/register`, `/v1/fetch_job`, `/v1/submit`.
- Runtime registration succeeds.
- At least one job completes and telemetry includes `job.end`.
- Credit preview logs are emitted without payout actions.
## Scope Boundary

Use this skill only for the `repo-a-coordinator-smoke` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## Reference

- `references/smoke-signals.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
