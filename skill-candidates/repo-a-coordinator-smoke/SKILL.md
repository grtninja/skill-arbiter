---
name: repo-a-coordinator-smoke
description: Run and debug Repo A DDC node/coordinator smoke workflows. Use when changing coordinator endpoints, job fetch/submit flow, runtime registration, or backend dispatch paths that must be verified with local coordinator execution.
---

# Repo A DDC Coordinator Smoke

Use this skill for local coordinator+node runtime validation.

## Workflow

1. Launch local coordinator stub.
2. Start node runtime with verbose policy path.
3. Set router-profile environment when validating network-aware dispatch:
   - `MESHGPT_ROUTER_MODE` (`ai_auto`, `gaming`, `streaming`, `wfh`, `traditional_qos`)
4. Confirm one embeddings flow completes.
5. Include coordinator health telemetry before/after startup:
   - `GET /health`
   - `POST /v1/register` readiness probe when credentials are configured
6. Verify telemetry emits expected lifecycle markers.
7. Verify NullClaw routing endpoints return deterministic profile-aligned decisions.

## Canonical Smoke Commands

Run from `<PRIVATE_REPO_A>` root:

```bash
uvicorn packages.coordinator.app.main:app --port 8787 --reload
```

In a second shell:

```bash
python -m repo_a_node --policy config/device_policy.json --verbose
```

Router-profile smoke (third shell):

```bash
$env:MESHGPT_ROUTER_MODE="wfh"
pytest -q tests/coordinator/test_nullclaw_routing.py
curl -s http://127.0.0.1:8787/v1/routing/nullclaw/decision
```

## Smoke Expectations

- Coordinator endpoints reachable: `/v1/register`, `/v1/fetch_job`, `/v1/submit`.
- `/health` reachable and returns a sane readiness state.
- Runtime registration succeeds.
- At least one job completes and telemetry includes `job.end`.
- Credit preview logs are emitted without payout actions.
- NullClaw routing payload includes `router_mode` and a stable routing rationale.
- Router mode aliases resolve consistently (`MESHGPT_NETWORK_PROFILE` mirrors `MESHGPT_ROUTER_MODE`).
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
