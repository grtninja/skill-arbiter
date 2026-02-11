---
name: skill-common-sense-engineering
description: Apply practical human common-sense checks before and after coding work. Use when you want to prevent avoidable mistakes, keep changes proportional, and capture obvious hygiene fixes during implementation.
---

# Common-Sense Engineering

Use this skill as a lightweight sanity layer for day-to-day coding work.

## Workflow

1. Clarify the real goal before choosing tools or edits.
2. Prefer the smallest change that satisfies the request.
3. Check local side effects before concluding:
   - generated artifacts (`__pycache__`, `*.pyc`, tool caches),
   - accidental temp/debug files,
   - obviously stale docs references.
4. If a repeatable issue appears during work, update the relevant skill/checklist in the same change.
5. Capture short evidence of what was checked and what was fixed.

## Common-Sense Checks

Run from repo root:

```bash
git status --short
python3 scripts/check_private_data_policy.py
```

Artifact hygiene scan:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter-lockdown-admission/scripts/artifact_hygiene_scan.py" . --fail-on-found
```

## Decision Heuristics

1. If two fixes work, choose the one with fewer moving parts.
2. If a change cannot be explained in one sentence, scope is probably too large.
3. If a failure can recur, codify it in a skill/workflow instead of relying on memory.
4. If evidence is missing, do not claim success.
## Scope Boundary

Use this skill only for the `skill-common-sense-engineering` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## References

- `references/common-sense-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
