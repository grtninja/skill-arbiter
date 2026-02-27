---
name: skill-enforcer
description: Enforce cross-repo policy and boundary alignment before completion. Use when a request touches multiple repositories, shared contracts, or policy docs that must stay synchronized.
---

# Skill Enforcer

Use this skill to fail closed on cross-repo policy drift.

## Workflow

1. Enumerate touched repositories and classify each change lane.
2. Read governing policy docs for each touched repo (`AGENTS.md`, `BOUNDARIES.md`, and repo-specific runbooks when present).
3. Validate required gates and doc lockstep rules for each lane.
4. Identify conflicts across repo policies, contracts, or required commands.
5. Report one consolidated pass/fail decision with explicit blockers.

## Required Checks

- Policy docs do not contradict each other for shared workflows.
- Shared API/schema contracts remain compatible across touched repos.
- Required validation commands are run (or explicitly blocked with target-host rerun steps).
- Placeholder and privacy rules are preserved in changed docs/skills.

## Commands

From this repo root (adjust paths as needed for other repos):

```bash
python3 scripts/check_private_data_policy.py
python3 scripts/check_release_hygiene.py
```

For cross-repo policy references:

```bash
rg -n "AGENTS.md|BOUNDARIES.md|SCOPE_TRACKER|HEARTBEAT.md|preflight" -S .
```

## Scope Boundary

Use this skill only for cross-repo policy enforcement and alignment checks.

Do not use this skill as a substitute for repository-specific implementation skills.

## References

- `references/policy-alignment-checklist.md`

## Loopback

If policy alignment is unresolved:

1. Capture the conflicting policies with file-level evidence.
2. Route back through `$skill-hub` with the conflict constraints.
3. Resume only when the chain has an explicit resolution path.
