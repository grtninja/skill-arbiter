---
name: "skills-third-party-intake"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Vet third-party skill catalogs with deterministic security and quality scoring before arbiter admission. Use when mining external repos (for example openclaw/nullclaw) for safe candidate imports."
---

# Skills Third-Party Intake

Use this skill to turn external skill catalogs into a safe, ranked intake list.

## Workflow

1. Scan one or more third-party skill roots.
2. Run deterministic checks inspired by hardened loaders:
   - frontmatter/schema hygiene
   - script/link risk markers
   - high-risk snippet detection
   - dependency/sensitive marker inventory
3. Score each skill for compatibility, quality, and security.
4. Produce an `admit` / `manual_review` / `reject` recommendation list.
5. Feed only `admit` candidates into `skill-installer-plus` + `skill-arbiter` lockdown admission.

## Intake Scan Command

```bash
python3 "$CODEX_HOME/skills/skills-third-party-intake/scripts/third_party_skill_intake.py" \
  --source-root openclaw=G:/_3rdParty-Clones/openclaw/skills \
  --source-root openclaw-ext=G:/_3rdParty-Clones/openclaw/extensions \
  --json-out /tmp/third-party-intake.json
```

## Review-Only Mode

```bash
python3 "$CODEX_HOME/skills/skills-third-party-intake/scripts/third_party_skill_intake.py" \
  --source-root /path/to/external/skills \
  --min-security 0.75 \
  --format table
```

## Admission Handoff

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  <skill> [<skill> ...] \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/skills-third-party-intake-arbiter.json
```

## Guardrails

- Fail closed on high-risk snippets and unsafe markdown links.
- Treat script-bearing third-party skills as manual review unless explicitly justified.
- Keep imports public-shape only; strip private paths and identifiers before commit.

## Scope Boundary

Use this skill only for third-party discovery and intake triage.

Do not install directly from third-party repos in this lane; route admitted candidates through `skill-arbiter` lockdown mode.

## References

- `references/intake-rubric.md`
