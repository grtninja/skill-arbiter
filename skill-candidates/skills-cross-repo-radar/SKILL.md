---
name: skills-cross-repo-radar
description: Run recurring multi-repo MX3/shim change scans and map signals to skill upgrades, consolidation, or new-candidate discovery. Use when you maintain multiple repos and want frequent evidence-backed skill curation.
---

# Skills Cross-Repo Radar

Use this skill to monitor recent repo activity and catch skill-update opportunities before drift accumulates.

## Workflow

1. Define the repositories to monitor (for example `<PRIVATE_REPO_A>`, `<PRIVATE_REPO_B>`, `<PRIVATE_REPO_C>`, `<PRIVATE_REPO_D>`).
2. Scan recent git commit subjects for MX3/shim/hardware/contract signals.
3. Review per-repo recommendations and sampled matching commits.
4. Route actions to:
   - `$skills-discovery-curation` for new-skill or upgrade discovery
   - `$skills-consolidation-architect` when trigger boundaries start overlapping
5. Admit changed/new skills with personal lockdown mode.

## Scan Command

```bash
python3 "$CODEX_HOME/skills/skills-cross-repo-radar/scripts/repo_change_radar.py" \
  --repo "<PRIVATE_REPO_A>=/path/to/<PRIVATE_REPO_A>" \
  --repo "<PRIVATE_REPO_B>=/path/to/<PRIVATE_REPO_B>" \
  --repo "<PRIVATE_REPO_C>=/path/to/<PRIVATE_REPO_C>" \
  --since-days 14 \
  --max-commits 160 \
  --json-out /tmp/skills-cross-repo-radar.json
```

## Follow-Up Admission

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" <skill> [<skill> ...] \
  --source-dir "$CODEX_HOME/skills" \
  --window 10 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

## References

- `references/radar-playbook.md`
- `scripts/repo_change_radar.py`
