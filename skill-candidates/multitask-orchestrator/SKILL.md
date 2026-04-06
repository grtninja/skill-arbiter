---
name: multitask-orchestrator
description: "Split multi-lane requests into deterministic parallel workstreams and merge them with explicit evidence checks. Use when a request has 2+ independent objectives that can run concurrently."
---

# Multitask Orchestrator

Use this skill when one request contains multiple independent lanes that should run in parallel.

## Trigger Conditions

Use `multitask-orchestrator` when all are true:

1. At least two lanes can proceed without blocking each other.
2. Each lane has a clear success artifact or pass/fail signal.
3. The final response must merge outcomes from all lanes.

Do not use this skill for single-lane work or tightly coupled sequential changes.

## Workflow

1. Define lanes with stable IDs (`lane-a`, `lane-b`, ...), owners, and expected outputs.
2. Assign each lane a minimal chain (`skill-hub` routed) and explicit guardrails.
3. Run lanes in parallel.
4. Capture per-lane evidence (artifacts, checks, unresolved risks).
5. Merge lanes only after all required gates pass.
6. If any lane blocks, route that lane through `request-loopback-resume` and continue non-blocked lanes.

## Lane Contract

Each lane must provide:

- `objective`: one sentence scope
- `inputs`: files/repos/skills used
- `checks`: commands or validation gates
- `artifacts`: JSON/log/doc paths
- `status`: `pass`, `fail`, or `blocked`
- `next_action`: deterministic follow-up

## Merge Rules

1. Merge only `pass` lanes.
2. `blocked` lanes require loopback state before completion.
3. `fail` lanes must include root cause and remediation lane.
4. Final response includes:
   - lane summary table
   - unresolved risks
   - exact artifact references

## Guardrails

- Keep lane scope minimal; avoid cross-lane file overlap when possible.
- Prefer deterministic scripts/evidence over free-form narrative.
- Healthy local OpenClaw-compatible subagents are preferred when a lane needs bounded sidecar analysis.
- If cloud sidecars are required, keep them lower-reasoning and low-cost.
- Do not suppress failing lane results to unblock completion.

## References

- `references/lane-contract.md`
