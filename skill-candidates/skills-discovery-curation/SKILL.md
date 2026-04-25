---
name: "skills-discovery-curation"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Discover, triage, and prioritize Codex skills for a repository or workspace. Use for one-time audits and recurring curation runs after cross-repo MX3/shim drift scans."
---

# Skills Discovery and Curation

Use this skill to build a practical skill portfolio for a repo.

## Workflow

1. Route the request through `$skill-hub` for baseline chain selection.
2. Capture the current meta-harness authority contract for the curation pass:
   - PC Control evidence/status surfaces first
   - canonical repo root `G:\GitHub` on the maintainer workstation
   - authoritative model lanes `http://127.0.0.1:9000/v1` and `http://127.0.0.1:2337/v1`
   - `http://127.0.0.1:1234/v1` only as a non-authoritative operator surface
3. Inventory available skills and currently installed skills.
4. If maintaining multiple repos, run `$skills-cross-repo-radar` first.
5. When the ask is about recent Codex work, inspect recent local workstreams/continuity artifacts as evidence in addition to git history.
6. Map repository workflows to missing capabilities.
7. Include practical baseline checks via `$skill-common-sense-engineering`.
8. Run `$usage-watcher` and capture usage mode plus analysis/plan artifacts.
9. Run `$skill-cost-credit-governor` and capture analysis/policy artifacts.
10. Run `$skill-cold-start-warm-path-optimizer` and capture cold/warm analysis/plan artifacts.
11. Include quality/compliance lanes where needed (`$skill-auditor`, `$skill-enforcer`).
12. For candidate additions/updates, classify each skill as `unique` vs `upgrade` using `$skill-auditor`.
13. Require arbiter evidence status `pass` before admitting candidates.
14. Propose a minimal prioritized skill set (core first, optional second) with usage guardrail status.
15. Provide admission plan using local `skill-arbiter` lockdown flow.
16. For meta-harness or whole-PC curation, normalize repo paths to `G:\GitHub`, capture PC Control status/evidence first, and treat `http://127.0.0.1:9000/v1` plus `http://127.0.0.1:2337/v1` as the authoritative model lanes.

## Discovery Commands

```bash
find $CODEX_HOME/skills -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
find $CODEX_HOME/skills -mindepth 1 -maxdepth 2 -name SKILL.md -type f | sort
```

Optional recurring cross-repo scan:

```bash
python3 "$CODEX_HOME/skills/skills-cross-repo-radar/scripts/repo_change_radar.py" \
  --repo "<PRIVATE_REPO_A>=/path/to/<PRIVATE_REPO_A>" \
  --repo "<PRIVATE_REPO_B>=/path/to/<PRIVATE_REPO_B>" \
  --since-days 14 \
  --json-out /tmp/skills-cross-repo-radar.json
```

## Curation Output Format

1. Current inventory summary.
2. Missing capability gaps by repo workflow.
3. Usage guardrail decision (`economy`/`standard`/`surge`) with JSON evidence paths from `usage-watcher`, `skill-cost-credit-governor`, and `skill-cold-start-warm-path-optimizer`.
4. Recommended skill candidates (ranked).
5. Admission command using `--personal-lockdown`.

## Admission Command Template

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" <skill> [<skill> ...] \
  --source-dir "$CODEX_HOME/skills" \
  --window 10 --threshold 3 --max-rg 3 \
  --personal-lockdown
```
## Scope Boundary

Use this skill only for the `skills-discovery-curation` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## Reference

- `references/discovery-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
