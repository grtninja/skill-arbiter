---
name: skills-consolidation-architect
description: Consolidate repository-specific skills into modular, reusable sets. Use when auditing skill overlap, splitting monolithic skills, reducing one-shot skills, defining per-repo core vs advanced skills, and planning safe deprecations with lockdown admission tests.
---

# Skills Consolidation Architect

Use this skill to keep your skill ecosystem modular and maintainable.

## Consolidation Workflow

1. Run `$skill-auditor` first for recent-change quality signals plus per-skill `unique` vs `upgrade` classification.
2. Inventory installed skills and group by repository domain.
3. Optionally ingest recent cross-repo radar results from `$skills-cross-repo-radar`.
4. Run `$usage-watcher`, `$skill-cost-credit-governor`, and `$skill-cold-start-warm-path-optimizer`; capture usage guardrail evidence before finalizing chain recommendations.
5. Run overlap audit and identify merge/split candidates.
6. Apply consolidation rubric:
   - keep single-responsibility skills,
   - split multi-workflow monoliths,
   - avoid near-duplicate trigger scopes.
7. Define per-repo sets:
   - `core`: always-on, high-frequency tasks,
   - `advanced`: specialized workflows,
   - `experimental`: new candidates pending arbiter evidence.
8. Ensure each repo `core` set includes explicit usage guardrail consideration and documented disposition for `usage-watcher`, `skill-cost-credit-governor`, and `skill-cold-start-warm-path-optimizer`.
9. Admit changed/new skills with `skill-arbiter --personal-lockdown`.
10. Fail closed when arbiter evidence is missing or not `pass`.

## Commands

Inventory installed skills:

```bash
find $CODEX_HOME/skills -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
```

Run overlap audit:

```bash
python3 scripts/skill_overlap_audit.py --skills-root $CODEX_HOME/skills --threshold 0.28
```

JSON output for automation:

```bash
python3 scripts/skill_overlap_audit.py \
  --skills-root $CODEX_HOME/skills \
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
- Missing usage-guardrail evidence: do not finalize chain recommendations.

Keep each repo’s `core` set between 3 and 6 skills by default.
## Scope Boundary

Use this skill only for the `skills-consolidation-architect` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## References

- `references/consolidation-rubric.md`
- `scripts/skill_overlap_audit.py`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
