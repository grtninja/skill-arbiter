---
name: repo-c-persona-registry-maintenance
description: Maintain persona pack discovery and manifest-driven stack loading in <PRIVATE_REPO_C>. Use when adding/updating persona packs, editing manifest.persona.json files, or changing registry loader behavior in repo_c/persona_registry.py.
---

# Repo C Persona Registry Maintenance

Use this skill for persona pack integrity and loader behavior.

## Workflow

1. Keep each persona pack manifest valid (`manifest.persona.json`).
2. Ensure `files_in_order` resolves to real pack files.
3. Verify loader functions discover and assemble persona stacks correctly.
4. Preserve backward-compatible persona selection behavior.

## Quick Validation Snippet

Run from `<PRIVATE_REPO_C>` root:

```bash
python - <<'PY'
from repo_c.persona_registry import list_personas, load_persona_stack
personas = list_personas()
print('count=', len(personas))
if personas:
    stack = load_persona_stack(personas[0].persona_id)
    print('persona=', stack['persona_id'], 'files=', len(stack['files']))
PY
```

## Contract Notes

- `list_personas()` discovers `*/manifest.persona.json`.
- `get_persona_files()` and `load_persona_stack()` must honor `files_in_order`.
- Missing persona files should fail loudly with actionable errors.
## Scope Boundary

Use this skill only for the `repo-c-persona-registry-maintenance` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## Reference

- `references/persona-registry-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
