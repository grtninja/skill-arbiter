---
name: skill-arbiter
description: Public candidate skill for arbitrating Codex skill installs on Windows hosts. Use when you need to reintroduce skills one-by-one, detect which skill triggers persistent rg.exe/CPU churn, and automatically remove or blacklist offending skills with reproducible evidence.
---

# Skill Arbiter

The St. Peter of skills.

Author: Edward Silvia  
License: MIT

Use this skill to decide which skills get admitted and which get quarantined.

## Run

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  doc screenshot security-best-practices security-threat-model playwright \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3
```

For personally-created skills:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  my-new-skill \
  --source-dir "$CODEX_HOME/skills" \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --promote-safe
```

For personal lockdown mode:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  my-new-skill \
  --source-dir "$CODEX_HOME/skills" \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

## Behavior

1. Install each candidate skill one-by-one from curated source.
2. Sample baseline `rg.exe` activity before each install and evaluate churn using delta-over-baseline samples.
3. Remove and blacklist offenders automatically.
4. Treat blacklisted skills as permanently denied and delete them if present.
5. Respect local whitelist entries in `<dest>/.whitelist.local` and skip arbitration for approved skills.
6. Respect local immutable entries in `<dest>/.immutable.local`; immutable skills are never removed/blacklisted.
7. Third-party (repo-based) skills are deny-by-default and deleted unless `--promote-safe` is used.
8. `--promote-safe` auto-adds passing skills to whitelist + immutable files.
9. Emit optional JSON evidence via `--json-out`.
10. `--personal-lockdown` requires local `--source-dir`, forces whitelist+immutable promotion, and rejects symlinked control files.

## Safe Modes

- Use `--dry-run` to preview actions without modifying files.
- Use `--dest` to test in an isolated skills directory.

## Mass-Index Skill Admission

Use this command to admit the bounded no-`rg` indexing skill family:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  safe-mass-index-core repo-b-mass-index-ops repo-d-mass-index-ops repo-c-mass-index-ops \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/mass-index-arbiter.json
```

Expected acceptance:

- `action=kept`
- `persistent_nonzero=false`
- `max_rg=0` target for each skill

## Usage-Watcher Admission

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  usage-watcher \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/usage-watcher-arbiter.json
```

## REPO_B Local Bridge Orchestrator Admission

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  repo-b-local-bridge-orchestrator \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/repo-b-local-bridge-orchestrator-arbiter.json
```

## REPO_B MCP Comfy Bridge Admission (Canonical)

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  repo-b-mcp-comfy-bridge \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/repo-b-mcp-comfy-bridge-arbiter.json
```

## REPO_B Comfy AMUSE CapCut Pipeline Admission

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  repo-b-comfy-amuse-capcut-pipeline \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/repo-b-comfy-amuse-capcut-pipeline-arbiter.json
```

## REPO_B Local Comfy Orchestrator Admission (Legacy Wrapper)

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  repo-b-local-comfy-orchestrator \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/repo-b-local-comfy-orchestrator-arbiter.json
```

## Meta-Governance Skill Pack Admission

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  skill-cost-credit-governor skill-dependency-fan-out-inspector \
  skill-cold-start-warm-path-optimizer skill-blast-radius-simulator skill-trust-ledger \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/skill-meta-governance-arbiter.json
```

## Cross-Repo Radar Admission

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  skills-cross-repo-radar \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/skills-cross-repo-radar-arbiter.json
```

## Code Gap Sweeping Admission

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  code-gap-sweeping \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/code-gap-sweeping-arbiter.json
```

## Request Loopback Resume Admission

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  request-loopback-resume \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/request-loopback-resume-arbiter.json
```

## Skill Governance System Admission

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  skill-hub skill-installer-plus skill-auditor skill-enforcer \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/skill-governance-system-arbiter.json
```

## Common-Sense Engineering Admission

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  skill-common-sense-engineering \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/skill-common-sense-engineering-arbiter.json
```

## Default System Chain

When starting new work, run this chain:

1. `$skill-hub` to route task -> skill chain.
2. `$skill-common-sense-engineering` baseline checks.
3. `$usage-watcher` to decide usage mode (`economy`/`standard`/`surge`) and emit usage analysis + plan JSON.
4. `$skill-cost-credit-governor` to evaluate per-skill spend/chatter risk and emit analysis + policy JSON.
5. `$skill-cold-start-warm-path-optimizer` to evaluate cold/warm latency and emit analysis + plan JSON.
6. `$code-gap-sweeping` for cross-repo implementation-gap scans before broad mutation lanes.
7. `$request-loopback-resume` to checkpoint/resume interrupted requests with deterministic next-lane actions.
8. `$skill-installer-plus` for local install planning, lockdown admission wrappers, and feedback-led recommendation updates.
9. `$multitask-orchestrator` when 2+ independent lanes are present.
10. `$skill-auditor` on new/changed skill surfaces.
11. `$skill-enforcer` for cross-repo policy alignment when operating across repos.
12. Loop unresolved lanes back through `$skill-hub` until convergence or max loop count.
13. Record XP/level with `python3 scripts/skill_game.py` using arbiter/auditor evidence JSON files.

## Skill Game Command

```bash
python3 scripts/skill_game.py \
  --task "skill candidate update" \
  --used-skill skill-hub \
  --used-skill skill-common-sense-engineering \
  --used-skill usage-watcher \
  --used-skill skill-cost-credit-governor \
  --used-skill skill-cold-start-warm-path-optimizer \
  --used-skill skill-installer-plus \
  --used-skill skill-auditor \
  --used-skill skill-enforcer \
  --used-skill skill-arbiter-lockdown-admission \
  --arbiter-report /tmp/skill-arbiter-evidence.json \
  --audit-report /tmp/skill-audit.json \
  --enforcer-pass
```

Mandatory skill-change gates:

1. Every new/updated skill must have `skill-arbiter-lockdown-admission` evidence (`action`, `persistent_nonzero`, `max_rg`) and a passing outcome.
2. Every new/updated skill must be classified by `$skill-auditor` as `unique` or `upgrade`.
3. `upgrade` classifications should update existing skill lanes unless strict boundary differences are documented.
4. Every new/updated skill should capture `skill-installer-plus` plan/admit outputs so recommendation quality improves run-over-run.
5. Every chain proposal must include usage guardrail evidence from `$usage-watcher`, `$skill-cost-credit-governor`, and `$skill-cold-start-warm-path-optimizer`; chaining is incomplete without this evaluation.

## Release Workflow

For release-impacting changes (for example `scripts/`, `SKILL.md`, or non-doc files):

```bash
python3 scripts/prepare_release.py --part patch
```

Then refine the new `CHANGELOG.md` entry for the PR.

CI enforces this on pull requests with:

```bash
python3 scripts/check_release_hygiene.py
```

## Privacy Lock

This repo is public-shape only. Do not commit private repo identifiers or user-specific absolute paths.

Local/staged check:

```bash
python3 scripts/check_private_data_policy.py --staged
```

CI check:

```bash
python3 scripts/check_private_data_policy.py
```

## Skill Level-Up Declaration

When this workflow creates or improves a skill, include this exact two-line declaration in the response:

```text
New Skill Unlocked: <SkillName>
<SkillName> Leveled up to <LevelNumber>
```
