---
name: docs-alignment-lock
description: Keep repository policy docs aligned and privacy-safe before PRs. Use when changing workflow/policy text across AGENTS.md, README.md, CONTRIBUTING.md, SKILL.md, PR templates, or skill candidate docs.
---

# Docs Alignment Lock

Use this skill to keep documentation policy-consistent and public-safe.

## Workflow

1. Read `AGENTS.md` first and treat it as policy source of truth.
2. Align policy language across:
   - `AGENTS.md`
   - `README.md`
   - `CONTRIBUTING.md`
   - `SKILL.md`
   - `.github/pull_request_template.md`
3. Enforce public-shape rules in docs and skill candidates:
   - no private repo identifiers
   - no user-specific absolute paths
   - use placeholders (`<PRIVATE_REPO_NAME>`, `$CODEX_HOME/skills`, `$env:USERPROFILE\\...`)
4. Ensure skill update messaging rule is present and aligned:
   - `New Skill Unlocked: <SkillName>`
   - `<SkillName> Leveled up to <LevelNumber>`
5. Run privacy and release checks.
6. If release-impacting docs/scripts changed, prepare a patch release bump.

## Commands

```bash
python3 scripts/check_private_data_policy.py
python3 scripts/check_release_hygiene.py
python3 -m py_compile scripts/arbitrate_skills.py scripts/prepare_release.py scripts/check_release_hygiene.py scripts/check_private_data_policy.py
```

For release-impacting changes:

```bash
python3 scripts/prepare_release.py --part patch
```

## Reference

- `references/docs-alignment-checklist.md`
