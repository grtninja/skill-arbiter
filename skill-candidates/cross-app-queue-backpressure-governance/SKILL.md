---
name: cross-app-queue-backpressure-governance
description: Govern queue ownership, backpressure, retry and cancel semantics, and mutual-exclusion behavior across STARFRAME local apps. Use when `9040`, `9041`, bridge queues, or operator queue surfaces change together.
---

# Cross-App Queue Backpressure Governance

Use this skill when queue behavior spans more than one STARFRAME app or worker surface.

## Workflow

1. Identify the true queue owners before changing any client surface.
2. Inspect queue depth, retry, cancel, and recovery behavior across the affected apps.
3. Check mutual-exclusion and heavy-lane ownership rules before enabling parallel execution.
4. Keep operator-visible queue state aligned with the backend owner.
5. Re-run a bounded queue proof after changes land.

## Required Evidence

- queue owners involved
- backpressure or mutual-exclusion rule touched
- retry, cancel, or recovery proof
- operator-visible queue/status surface checked

## Guardrails

- Do not invent a second queue owner.
- Do not let a client redefine retry or cancel rules owned elsewhere.
- Fail closed if queue truth and UI truth drift.
- Keep heavy-lane exclusivity explicit when `9040` and `9041` are involved.

## Best-Fit Companion Skills

- `$media-workbench-worker-contracts`
- `$qwen-training-campaign-ops`
- `$repo-b-avatarcore-ops`
- `$skill-common-sense-engineering`

## Scope Boundary

Use this skill only for cross-app queue ownership, backpressure, and recovery governance.

For a single repo's queue contract, route to that repo's more specific worker skill.
