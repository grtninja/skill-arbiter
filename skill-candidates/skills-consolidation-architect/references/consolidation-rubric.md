# Skill Consolidation Rubric

## 1) Modular by Responsibility

A skill should own one primary concern:
- release ops,
- policy/schema validation,
- runtime smoke,
- routing diagnostics,
- security/privacy guardrails,
- packaging/build.

If a skill requires multiple unrelated workflows to explain itself, split it.

## 2) Trigger Precision

Frontmatter descriptions should answer:
- what does this skill do,
- when exactly should it trigger,
- what files/systems are in scope.

Two skills with similar trigger language usually need consolidation.

## 3) Repo Skill Set Shape

For each repository:
- `core` (3-6 skills): high-frequency workflows.
- `advanced`: specialized operations.
- `experimental`: candidates not yet pinned immutable.

## 4) Deprecation Discipline

When consolidating:
1. create replacement skill(s),
2. run arbiter admission tests,
3. migrate usage to replacement,
4. remove deprecated skill from whitelist/immutable only after replacement is proven.

## 5) Evidence-Backed Decisions

Use overlap scores plus practical usage frequency.
Do not merge skills only by text similarity if runtime responsibilities are different.
