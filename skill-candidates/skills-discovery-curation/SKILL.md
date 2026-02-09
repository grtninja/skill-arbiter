---
name: skills-discovery-curation
description: Discover, triage, and prioritize Codex skills for a repository or workspace. Use when auditing existing skills, identifying missing capabilities, mapping skills to repo workflows, and generating a safe install/admission plan.
---

# Skills Discovery and Curation

Use this skill to build a practical skill portfolio for a repo.

## Workflow

1. Inventory available skills and currently installed skills.
2. Map repository workflows to missing capabilities.
3. Propose a minimal prioritized skill set (core first, optional second).
4. Provide admission plan using local `skill-arbiter` lockdown flow.

## Discovery Commands

```bash
find /home/eddie/.codex/skills -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
find /home/eddie/.codex/skills -mindepth 1 -maxdepth 2 -name SKILL.md -type f | sort
```

## Curation Output Format

1. Current inventory summary.
2. Missing capability gaps by repo workflow.
3. Recommended skill candidates (ranked).
4. Admission command using `--personal-lockdown`.

## Admission Command Template

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" <skill> [<skill> ...] \
  --source-dir "$CODEX_HOME/skills" \
  --window 10 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

## Reference

- `references/discovery-checklist.md`
