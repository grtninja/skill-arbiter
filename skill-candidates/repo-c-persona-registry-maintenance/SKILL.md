---
name: starframe-persona-registry-maintenance
description: Maintain persona pack discovery and manifest-driven stack loading in <STARFRAME_REPO>. Use when adding/updating persona packs, editing manifest.persona.json files, or changing registry loader behavior in starframe/persona_registry.py.
---

# STARFRAME Persona Registry Maintenance

Use this skill for persona pack integrity and loader behavior.

## Workflow

1. Keep each persona pack manifest valid (`manifest.persona.json`).
2. Ensure `files_in_order` resolves to real pack files.
3. Verify loader functions discover and assemble persona stacks correctly.
4. Preserve backward-compatible persona selection behavior.

## Quick Validation Snippet

Run from `<STARFRAME_REPO>` root:

```bash
python - <<'PY'
from starframe.persona_registry import list_personas, load_persona_stack
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

## Reference

- `references/persona-registry-checklist.md`
