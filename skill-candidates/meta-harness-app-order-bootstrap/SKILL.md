---
name: meta-harness-app-order-bootstrap
description: Orchestrate app-first, registry-aware bring-up and health validation for local multi-app meta-harness stacks. Use when startup order, runtime registry, launcher scripts, control-center bring-up, or cross-app health checks change together.
---

# Meta-Harness App-Order Bootstrap

Use this skill when recent work spans startup scripts, runtime registries, app-order sequencing, and cross-app health validation under the local meta-harness.

## Trigger Conditions

Use this skill when all are true:

1. Two or more local apps/services must launch or attach in a required order.
2. The work touches launcher scripts, runtime registry state, or desktop bring-up flows.
3. Validation depends on real endpoint health, not just process start.

Route elsewhere when:

- the task is only about desktop window polish or shortcut ownership: use `$desktop-startup-acceptance`
- the task is only about one repo's internal routing contract: use the most specific repo skill
- the task is only about model-lane authority drift: use `$shim-pc-control-brain-routing`

## Workflow

1. Capture the intended app order and ownership:
   - app-first entry surface
   - attach/start sequence
   - runtime registry updates
   - health and readiness gates
2. Read the active launcher and registry surfaces before editing.
3. Confirm the authoritative local model lanes:
   - `http://127.0.0.1:9000/v1`
   - `http://127.0.0.1:2337/v1`
   - treat `http://127.0.0.1:1234/v1` only as a non-authoritative operator surface
4. Patch sequencing, registry, or health contracts without introducing alternate public endpoints.
5. Validate the real bring-up flow in order:
   - launcher starts cleanly
   - dependent app attach succeeds
   - runtime registry reflects the active state
   - health endpoints stay green
6. Report the exact app-order contract and remaining degraded lanes.

## Required Evidence

- launcher files touched
- runtime registry files or templates touched
- health endpoints checked with status results
- any startup-order dependency that remains manual or operator-confirmed

## Guardrails

- Do not invent new public ports to work around sequencing bugs.
- Keep launch ownership explicit; one surface owns startup, dependent surfaces attach.
- Prefer shell-free public launch surfaces when desktop startup is involved.
- Fail closed when the registry says one thing and the live health surface says another.

## Scope Boundary

Use this skill for meta-harness bring-up sequencing, registry-aware startup contracts, and cross-app readiness validation.

Do not use this skill for unrelated packaging, UI styling, or long-running host offload work.

## References

- `$desktop-startup-acceptance`
- `$shim-pc-control-brain-routing`
- `$heterogeneous-stack-validation`
