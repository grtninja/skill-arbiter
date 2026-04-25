---
name: "skills-cross-repo-radar"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Detect recent cross-repo work and produce deterministic JSON evidence for skill curation and routing decisions. Use when workflows span multiple repos and you need a bounded view of recent commits, touched files, and policy/contract-sensitive changes."
---

# Skills Cross-Repo Radar

Use this skill to produce a bounded cross-repo snapshot of recent changes.

## Workflow

1. Define target repositories with one or more `--repo name=path` arguments.
2. Run the radar script with a bounded lookback window.
3. Review output for:
   - policy-sensitive changes,
   - API/contract surface touches,
   - skills/runtime lane changes,
   - repositories with highest churn.
4. Feed JSON evidence into discovery/consolidation lanes before adding or changing skills.

## Command

```bash
python3 "$CODEX_HOME/skills/skills-cross-repo-radar/scripts/repo_change_radar.py" \
  --repo "repo-a=/path/to/repo-a" \
  --repo "repo-b=/path/to/repo-b" \
  --since-days 14 \
  --json-out /tmp/skills-cross-repo-radar.json
```

## Scope Boundary

Use this skill only for cross-repo change radar and recent-work evidence generation.

Do not use this skill to modify repositories directly.

## Reference

- `references/output-contract.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture failure context and command stderr.
2. Route back through `$skill-hub` with narrowed repo scope.
3. Resume only after an explicit deterministic repo list is available.
