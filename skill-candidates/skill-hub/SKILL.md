---
name: "skill-hub"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Route user requests into the smallest deterministic skill chain. Use when work spans multiple domains or repositories, when lane selection is ambiguous, or when you need ordered skill handoff and loopback criteria before execution."
---

# Skill Hub

Use this skill as the entry router for skill chaining.

## Workflow

1. Parse request scope (repositories, domains, risk level, and deliverables).
2. For meta-harness or large-system work, capture the current local authority contract first:
   - treat `G:\GitHub` as the canonical repo root on the maintainer workstation
   - treat `http://127.0.0.1:9000/v1` and `http://127.0.0.1:2337/v1` as authoritative model lanes
   - treat `http://127.0.0.1:1234/v1` only as a non-authoritative operator surface
3. Select skills from the routing matrix below and keep the chain to the minimum set that fully covers the request.
4. Order the chain as: routing -> guardrails -> execution -> release/policy gates.
5. Emit or capture the chain output contract before execution begins.
6. Add loopback criteria for unresolved lanes before execution starts.

## Routing Matrix

| Scenario | Example Request | Chain Pattern |
| -------- | --------------- | ------------- |
| Single-repo, low risk | "Fix a bug in the admin terminal" | `skill-hub` -> `repo-a-host-admin-ops` -> `skill-common-sense-engineering` |
| Multi-repo, policy risk | "Sync packaging across repo-A and repo-D" | `skill-hub` -> `usage-watcher` + `skill-cost-credit-governor` -> execution skills -> `skill-enforcer` |
| New or changed skills | "Create a new overlay skill for Blender" | `skill-hub` -> guardrails -> `skill-creator-openclaw` -> `skill-auditor` -> `skill-arbiter-lockdown-admission` |
| Interrupted work | "Continue the release prep from yesterday" | `skill-hub` -> `request-loopback-resume` -> remaining lanes |
| Independent lanes | "Update docs AND run host validation" | split into parallel chains; merge only after per-lane evidence is present |

## Chain Rules

- Prefer one primary execution skill per independent lane.
- Avoid optional skills unless they add deterministic value for the request.
- For multi-repo work, include a policy-enforcement lane before finalizing code changes.
- For new or updated skills, include auditing and lockdown-admission lanes.
- Prefer healthy local OpenClaw-compatible subagents first for quick bounded sidecar work.
- When cloud sidecars are unavoidable, keep them on a lower-reasoning, low-cost sidecar lane.
- For whole-PC or meta-harness tasks, capture PC Control local-agent or status-surface evidence before assuming missing context.
- If a required skill is missing, fail closed with a bounded fallback and record the gap.

## Chain Output Contract

Emit or capture a compact chain payload before execution:

- `task`
- `lanes[]` (ordered lane identifiers)
- `skills_by_lane`
- `evidence_paths[]` (usage/cost/cold-warm + audit/arbiter when applicable)
- `loopback_criteria`
- `stop_conditions` (done, blocked, reroute)

Illustrative example:

```json
{
  "task": "update host packaging and add new overlay skill",
  "lanes": ["host-packaging", "skill-creation"],
  "skills_by_lane": {
    "host-packaging": ["repo-a-host-admin-ops", "skill-common-sense-engineering"],
    "skill-creation": ["skill-creator-openclaw", "skill-auditor", "skill-arbiter-lockdown-admission"]
  },
  "evidence_paths": [
    "/tmp/usage-analysis.json",
    "/tmp/usage-plan.json",
    "/tmp/skill-cost-analysis.json",
    "/tmp/skill-cost-policy.json",
    "/tmp/cold-warm-analysis.json",
    "/tmp/cold-warm-plan.json"
  ],
  "loopback_criteria": "re-route if host validation fails or audit blocks admission",
  "stop_conditions": ["all lanes emit evidence", "blocked lane triggers loopback", "operator cancels"]
}
```

If this contract is incomplete, chain selection is incomplete and must fail closed.

## Referenced Skills

Key skills this hub routes to (see each skill's SKILL.md for full details):

- **Guardrails**: `usage-watcher`, `skill-cost-credit-governor`, `skill-cold-start-warm-path-optimizer`
- **Execution**: `repo-a-host-admin-ops`, `repo-b-*` skills, `skill-creator-openclaw`, domain-specific skills
- **Policy gates**: `skill-enforcer`, `skill-arbiter-lockdown-admission`, `skill-auditor`
- **Resume**: `request-loopback-resume`
- **Hygiene**: `skill-common-sense-engineering`

## Scope Boundary

Use this skill only for request-to-chain routing and loopback decisioning.

Do not use this skill to implement repository changes directly.

## Loopback

If any lane remains unresolved, blocked, or ambiguous:

1. Capture lane blockers and current evidence.
2. Re-run routing through `$skill-hub` with updated constraints.
3. Resume only when every lane has a deterministic next action.
