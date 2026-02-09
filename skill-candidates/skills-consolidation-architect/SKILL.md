---
name: skills-consolidation-architect
description: Consolidate repository-specific skills into modular, reusable sets. Use when auditing skill overlap, splitting monolithic skills, reducing one-shot skills, defining per-repo core vs advanced skills, and planning safe deprecations with lockdown admission tests.
---

# Skills Consolidation Architect

Use this skill to keep your skill ecosystem modular and maintainable.

## Consolidation Workflow

1. Inventory installed skills and group by repository domain.
2. Run overlap audit and identify merge/split candidates.
3. Apply consolidation rubric:
   - keep single-responsibility skills,
   - split multi-workflow monoliths,
   - avoid near-duplicate trigger scopes.
4. Define per-repo sets:
   - `core`: always-on, high-frequency tasks,
   - `advanced`: specialized workflows,
   - `experimental`: new candidates pending arbiter evidence.
5. Admit changed/new skills with `skill-arbiter --personal-lockdown`.

## Commands

Inventory installed skills:

```bash
find /home/eddie/.codex/skills -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
```

Run overlap audit:

```bash
python3 scripts/skill_overlap_audit.py --skills-root /home/eddie/.codex/skills --threshold 0.28
```

JSON output for automation:

```bash
python3 scripts/skill_overlap_audit.py \
  --skills-root /home/eddie/.codex/skills \
  --threshold 0.28 \
  --json-out /tmp/skill-overlap.json
```

Admit consolidated candidates safely:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" <skill> [<skill> ...] \
  --source-dir "$CODEX_HOME/skills" \
  --window 10 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

## Decision Rules

- `score >= 0.55`: likely duplicate; merge or retire one.
- `0.35 <= score < 0.55`: boundary blur; tighten descriptions/scope.
- `score < 0.35`: generally distinct.

Keep each repo’s `core` set between 3 and 6 skills by default.

## References

- `references/consolidation-rubric.md`
- `scripts/skill_overlap_audit.py`
