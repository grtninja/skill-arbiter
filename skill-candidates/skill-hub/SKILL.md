---
name: skill-hub
description: Route user requests into the smallest deterministic skill chain. Use when work spans multiple domains or repositories, when lane selection is ambiguous, or when you need ordered skill handoff and loopback criteria before execution.
---

# Skill Hub

Use this skill as the entry router for skill chaining.

## Workflow

1. Parse request scope (repositories, domains, risk level, and deliverables).
2. Select the minimum set of skills that fully covers the request.
3. Order skills as: routing -> guardrails -> execution -> release/policy gates.
4. Add loopback criteria for unresolved lanes before execution begins.
5. Capture required evidence paths for usage guardrail lanes (usage watcher, cost governor, and cold-start warm-path optimizer).

## Routing Matrix

Use this fast matrix before final chain output:

1. Single-repo + low risk: routing lane -> execution lane -> validation lane.
2. Multi-repo + policy risk: routing lane -> usage/cost/cold-warm guardrails -> execution lanes -> policy-enforcement lane.
3. New or changed skills: routing lane -> guardrails -> execution -> audit lane -> lockdown-admission lane.
4. Interrupted work: routing lane -> resume lane -> remaining deterministic lanes.
5. Independent lanes: split into parallel chains; merge only after per-lane evidence is present.

## Chain Rules

- Prefer one primary execution skill per independent lane.
- Avoid optional skills unless they add deterministic value for the request.
- For multi-repo work, include a policy-enforcement lane before finalizing code changes.
- For new or updated skills, include auditing and lockdown-admission lanes.
- If a required skill is missing, fail closed with a bounded fallback and record the gap.

## Chain Output Contract

Emit or capture a compact chain payload before execution:

- `task`
- `lanes[]` (ordered lane identifiers)
- `skills_by_lane`
- `evidence_paths[]` (usage/cost/cold-warm + audit/arbiter when applicable)
- `loopback_criteria`
- `stop_conditions` (done, blocked, reroute)

If this contract is incomplete, chain selection is incomplete and must fail closed.

## Scope Boundary

Use this skill only for request-to-chain routing and loopback decisioning.

Do not use this skill to implement repository changes directly.

## Loopback

If any lane remains unresolved, blocked, or ambiguous:

1. Capture lane blockers and current evidence.
2. Re-run routing through `$skill-hub` with updated constraints.
3. Resume only when every lane has a deterministic next action.
