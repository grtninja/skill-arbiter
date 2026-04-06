---
name: skill-hub
description: "Coordinate multi-step workflows by routing requests into ordered skill chains — runs audits, enforces fixes, then updates docs automatically. Use when a task requires multiple tools or steps, when automating a batch pipeline across different repos, when delegating to specialized skills like usage-watcher or skill-auditor, when picking up interrupted work, or when the user says 'do X then Y' across code, docs, and policy."
---

# Skill Hub

Coordinates complex requests by breaking them into ordered skill chains. Routes each part of a request to the right specialized skill, defines completion criteria, and handles re-routing when steps get blocked.

## Workflow

1. **Parse request scope** — identify which repositories, domains (code, docs, policy, infra), risk level, and deliverables are involved.
2. **Select skills** from the routing matrix below — pick the minimum set that fully covers the request.
3. **Order the chain**: routing skills first, then guardrails (`usage-watcher`, `skill-cost-credit-governor`, `skill-cold-start-warm-path-optimizer`), then execution skills, then policy gates (`skill-enforcer`, `skill-arbiter-lockdown-admission`).
4. **Emit chain contract** before any execution starts:
   ```json
   {
     "task": "update host packaging and add new overlay skill",
     "lanes": ["host-packaging", "skill-creation"],
     "skills_by_lane": {
       "host-packaging": ["repo-a-host-admin-ops", "skill-common-sense-engineering"],
       "skill-creation": ["skill-creator-openclaw", "skill-auditor", "skill-arbiter-lockdown-admission"]
     },
     "evidence_paths": ["/tmp/usage-analysis.json", "/tmp/skill-cost-analysis.json"],
     "loopback_criteria": "re-route if host validation fails or audit blocks admission",
     "stop_conditions": ["all lanes emit evidence", "blocked lane triggers loopback", "operator cancels"]
   }
   ```
5. **Fail closed** if the contract is incomplete — every field must be populated. Record the gap and suggest a bounded fallback.

## Routing Matrix

| Scenario | Example Request | Chain Pattern |
| -------- | --------------- | ------------- |
| Single-repo, low risk | "Fix a bug in the admin terminal" | `skill-hub` -> `repo-a-host-admin-ops` -> `skill-common-sense-engineering` |
| Multi-repo, policy risk | "Sync packaging across repo-A and repo-D" | `skill-hub` -> `usage-watcher` + `skill-cost-credit-governor` -> execution skills -> `skill-enforcer` |
| New or changed skills | "Create a new overlay skill for Blender" | `skill-hub` -> guardrails -> `skill-creator-openclaw` -> `skill-auditor` -> `skill-arbiter-lockdown-admission` |
| Interrupted work | "Continue the release prep from yesterday" | `skill-hub` -> `request-loopback-resume` -> remaining lanes |
| Independent lanes | "Update docs AND run host validation" | split into parallel chains; merge only after per-lane evidence is present |

## Chain Rules

- One primary execution skill per independent lane.
- Skip optional skills unless they add concrete value for the specific request.
- Multi-repo work requires `skill-enforcer` before finalizing code changes.
- New or updated skills require `skill-auditor` and `skill-arbiter-lockdown-admission`.
- If a required skill is missing, fail closed with a bounded fallback and record the gap.

## Referenced Skills

Key skills this hub routes to (see each skill's SKILL.md for full details):

- **Guardrails**: `usage-watcher`, `skill-cost-credit-governor`, `skill-cold-start-warm-path-optimizer`
- **Execution**: `repo-a-host-admin-ops`, `repo-b-*` skills, `skill-creator-openclaw`, domain-specific skills
- **Policy gates**: `skill-enforcer`, `skill-arbiter-lockdown-admission`, `skill-auditor`
- **Resume**: `request-loopback-resume`
- **Hygiene**: `skill-common-sense-engineering`

## Scope Boundary

Use this skill only for request-to-chain routing. Do not use it to implement repository changes directly — delegate to the execution skills in the chain.

## Loopback

If any part of the chain is blocked or ambiguous:

1. Capture blockers and current evidence from the stuck lane.
2. Re-run routing through `$skill-hub` with updated constraints.
3. Resume only when every lane has a concrete next action.
