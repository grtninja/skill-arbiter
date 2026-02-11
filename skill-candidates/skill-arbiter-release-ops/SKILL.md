---
name: skill-arbiter-release-ops
description: Run release bump and PR release-hygiene workflow in skill-arbiter. Use when changes are release-impacting and require synchronized pyproject version, changelog entry, and CI release gate compliance.
---

# Skill Arbiter Release Ops

Use this skill for release-prep and release gate compliance.

## Workflow

1. Bump version and scaffold changelog notes.
2. Refine changelog notes to match behavior changes.
3. Run release hygiene check against base branch.
4. Run quick command and syntax checks.

## Commands

```bash
python3 scripts/prepare_release.py --part patch
python3 scripts/check_release_hygiene.py --base-ref main
python3 scripts/arbitrate_skills.py --help
python3 -m py_compile scripts/arbitrate_skills.py scripts/prepare_release.py scripts/check_release_hygiene.py
```

## Output Requirements

- `pyproject.toml` version increases.
- Top `CHANGELOG.md` heading matches new version.
- `check_release_hygiene.py` exits cleanly for PR context.
## Scope Boundary

Use this skill only for the `skill-arbiter-release-ops` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## Reference

- `references/release-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
