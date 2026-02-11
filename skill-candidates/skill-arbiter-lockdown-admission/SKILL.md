---
name: skill-arbiter-lockdown-admission
description: Install and admit-test local skills with strict personal policy in the skill-arbiter repo. Use when adding or updating personal skills, requiring local-only sources, pre-admission artifact cleanup, immutable pinning, blacklist quarantine, and rg.exe churn evidence.
---

# Skill Arbiter Lockdown Admission

Use this skill to admit local skills safely.

## Workflow

1. Validate candidate skill folders and names.
2. Run artifact hygiene scan and remove generated cache artifacts before admission evidence capture.
3. Run arbitration in local-only lockdown mode.
4. Confirm pass/fail actions and persisted lists.
5. Keep only passing skills whitelisted and immutable.

## Maintenance Trigger

When generated artifacts are discovered during real work (for example `__pycache__` or `*.pyc`), update this skill's checklist/script in the same change so cleanup behavior improves over time.

## Artifact Hygiene

Scan candidate roots for generated artifacts:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter-lockdown-admission/scripts/artifact_hygiene_scan.py" \
  /path/to/local/skills \
  --fail-on-found \
  --json-out /tmp/arbiter-artifact-scan.json
```

Remove findings deterministically:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter-lockdown-admission/scripts/artifact_hygiene_scan.py" \
  /path/to/local/skills \
  --apply \
  --json-out /tmp/arbiter-artifact-clean.json
```

## Canonical Command

```bash
python3 scripts/arbitrate_skills.py <skill> [<skill> ...] \
  --source-dir /path/to/local/skills \
  --dest $CODEX_HOME/skills \
  --window 10 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/arbiter-report.json
```

## Evidence Requirements

- Artifact hygiene report (`--json-out`) and cleanup evidence if artifacts were found.
- CSV result row for each skill.
- JSON report with `max_rg`, `persistent_nonzero`, `action`, and `note`.
- Updated `.whitelist.local` and `.immutable.local` entries for passing skills.
## Scope Boundary

Use this skill only for the `skill-arbiter-lockdown-admission` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## Reference

- `references/admission-checklist.md`
- `scripts/artifact_hygiene_scan.py`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
