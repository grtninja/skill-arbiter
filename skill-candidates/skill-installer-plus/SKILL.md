---
name: skill-installer-plus
description: Run local-first skill installation with lockdown admission and a learning recommendation loop. Use when adding/updating skills so installs are evidence-gated and future install choices improve from prior outcomes.
---

# Skill Installer Plus

Use this skill to streamline safe skill installs and continuously improve install decisions.

## Workflow

1. Generate a recommendation plan from local candidates and prior outcomes.
2. Evaluate usage guardrails with `$usage-watcher`, `$skill-cost-credit-governor`, and `$skill-cold-start-warm-path-optimizer` before final admit decisions.
3. Admit selected skills through `skill-arbiter` in personal-lockdown mode.
4. Persist outcomes to the installer ledger and optionally ingest trust-ledger events.
5. Record manual post-install feedback after real usage.

## Plan Recommendations

```bash
python3 "$CODEX_HOME/skills/skill-installer-plus/scripts/skill_installer_plus.py" \
  --ledger "$CODEX_HOME/skills/.skill-installer-plus-ledger.json" \
  plan \
  --skills-root skill-candidates \
  --dest "$CODEX_HOME/skills" \
  --trust-report /tmp/skill-trust-report.json \
  --json-out /tmp/skill-installer-plus-plan.json
```

## Admit Skills

```bash
python3 "$CODEX_HOME/skills/skill-installer-plus/scripts/skill_installer_plus.py" \
  --ledger "$CODEX_HOME/skills/.skill-installer-plus-ledger.json" \
  admit \
  --skill skill-installer-plus \
  --source-dir skill-candidates \
  --dest "$CODEX_HOME/skills" \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --arbiter-json /tmp/skill-installer-plus-arbiter.json \
  --json-out /tmp/skill-installer-plus-admit.json
```

Batch admit from a curated list:

```bash
python3 "$CODEX_HOME/skills/skill-installer-plus/scripts/skill_installer_plus.py" \
  --ledger "$CODEX_HOME/skills/.skill-installer-plus-ledger.json" \
  admit \
  --skills-file /tmp/candidate-skills.txt \
  --source-dir skill-candidates \
  --dest "$CODEX_HOME/skills" \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --arbiter-json /tmp/skill-installer-plus-arbiter-batch.json \
  --json-out /tmp/skill-installer-plus-admit-batch.json
```

## Record Manual Feedback

```bash
python3 "$CODEX_HOME/skills/skill-installer-plus/scripts/skill_installer_plus.py" \
  --ledger "$CODEX_HOME/skills/.skill-installer-plus-ledger.json" \
  feedback \
  --skill skill-installer-plus \
  --event success \
  --note "real workflow stable" \
  --json-out /tmp/skill-installer-plus-feedback.json
```

## Show Ledger State

```bash
python3 "$CODEX_HOME/skills/skill-installer-plus/scripts/skill_installer_plus.py" \
  --ledger "$CODEX_HOME/skills/.skill-installer-plus-ledger.json" \
  show \
  --recent 10 \
  --json-out /tmp/skill-installer-plus-show.json
```

## Scope Boundary

Use this skill only for the `skill-installer-plus` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

Admission decision is incomplete without usage guardrail evidence paths from `usage-watcher`, `skill-cost-credit-governor`, and `skill-cold-start-warm-path-optimizer`.

## Evidence Contract

For each admit cycle, keep:

- `plan_json`
- `admit_json`
- `arbiter_json`
- `trust_ingest_status`
- optional `feedback_json`

If any required artifact is missing, installation governance is incomplete.

## References

- `references/learning-loop.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
