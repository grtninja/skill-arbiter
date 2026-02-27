---
name: skill-auditor
description: Audit skill candidates and classify each changed skill as unique or upgrade with severity findings. Use when creating/updating skills, preparing admission evidence, or producing audit JSON for skill-game scoring.
---

# Skill Auditor

Use this skill to classify and gate new or updated skills.

## Workflow

1. Select changed skills (`--include-skill`) or scan the full candidate set.
2. Run the skill audit script to classify each skill as `unique` or `upgrade`.
3. Validate core quality checks:
   - frontmatter completeness (`name`, `description`),
   - `agents/openai.yaml` presence,
   - size/readability guardrails,
   - required arbiter evidence when enabled.
4. Review findings by severity (`high`, `medium`, `low`) and fix failures.
5. Re-run until `high_count=0` for admission-ready output.

## Commands

Audit selected skills:

```bash
python3 scripts/skill_audit.py \
  --skills-root skill-candidates \
  --include-skill <skill-name> \
  --json-out /tmp/skill-audit.json
```

Audit with arbiter evidence required:

```bash
python3 scripts/skill_audit.py \
  --skills-root skill-candidates \
  --include-skill <skill-name> \
  --arbiter-report /tmp/skill-arbiter-evidence.json \
  --require-arbiter-evidence \
  --json-out /tmp/skill-audit.json
```

## Classification Rules

- `unique`: no strong near-peer overlap detected in current skill set.
- `upgrade`: near-peer overlap indicates refinement/extension of an existing lane.
- `high` findings block completion.
- `medium` findings should be addressed before admission when possible.

## Scope Boundary

Use this skill only for skill-audit classification and findings generation.

Do not use this skill for runtime skill arbitration; use `$skill-arbiter-lockdown-admission`.

## References

- `references/audit-rubric.md`
- `scripts/skill_audit.py`

## Loopback

If findings remain unresolved:

1. Capture failing checks and evidence paths.
2. Route through `$skill-hub` for chain recalculation.
3. Resume only after an updated chain assigns deterministic fixes.
