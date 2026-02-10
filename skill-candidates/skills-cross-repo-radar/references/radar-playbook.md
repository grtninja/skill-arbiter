# Cross-Repo Radar Playbook

Use this playbook for recurring MX3/shim skill maintenance across multiple repositories.

## Cadence

1. Weekly scan for active development phases.
2. Biweekly scan for maintenance phases.
3. Monthly scan minimum for long-lived repositories.

## Signal Thresholds

Interpret `repo_change_radar.py` output using these defaults:

1. `total_hits = 0`:
   - No immediate skill changes needed.
2. `1 <= total_hits < 6`:
   - Upgrade existing skills only.
3. `total_hits >= 6`:
   - Run discovery for possible new skill candidates and scope splits.
4. `active_repos >= 2`:
   - Prioritize shared cross-repo skills before creating repo-specific one-off skills.

## Triage Targets

1. `mx3` + `mcp_bridge` hits:
   - Review `repo-b-mcp-comfy-bridge` and `repo-b-local-bridge-orchestrator`.
2. `hardware` hits:
   - Review `repo-b-hardware-first`.
3. `contracts` hits:
   - Review `repo-c-shim-contract-checks`.

## Required Follow-Ups

1. If discovery suggests additions/upgrades, run:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" <skill> [<skill> ...] \
  --source-dir "$CODEX_HOME/skills" \
  --window 10 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

2. If overlap is suspected, run:

```bash
python3 scripts/skill_overlap_audit.py --skills-root "$CODEX_HOME/skills" --threshold 0.28
```
