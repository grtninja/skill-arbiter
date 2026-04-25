---
name: "skill-common-sense-engineering"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Apply practical sanity checks before and after coding work to prevent avoidable mistakes. Use when verifying dependency surfaces, cleaning generated artifacts, checking privacy policy compliance, auditing artifact hygiene, or ensuring multi-skill chain guardrail evidence is present before claiming readiness."
---

# Common-Sense Engineering

Lightweight sanity layer for day-to-day coding work. Prevents avoidable mistakes by enforcing pre/post checks on every change.

## Workflow

1. **Clarify the goal** — state the objective in one sentence before choosing tools or edits.
2. **Audit dependency surface** — trace related contracts, dependents, and operator-facing surfaces before deciding the implementation boundary.
3. **Execute the change** — prefer existing scripts/workflows over ad hoc steps.
4. **Run common-sense checks** before concluding:
   ```bash
   git status --short
   python3 scripts/check_private_data_policy.py
   python3 "$CODEX_HOME/skills/skill-arbiter-lockdown-admission/scripts/artifact_hygiene_scan.py" . --fail-on-found
   ```
5. **Verify guardrail evidence** for multi-skill chains:
   ```bash
   test -f /tmp/usage-analysis.json && test -f /tmp/usage-plan.json
   test -f /tmp/skill-cost-analysis.json && test -f /tmp/skill-cost-policy.json
   test -f /tmp/cold-warm-analysis.json && test -f /tmp/cold-warm-plan.json
   ```
6. **Capture evidence** — summarize what was checked, what was fixed, and any unresolved risks.
7. If a repeatable issue appeared, update the relevant skill or checklist in the same change.

## Decision Heuristics

1. Between two fixes, choose the one that leaves the dependency graph clearer.
2. If a change cannot be explained in one sentence, document the scope rather than under-fixing.
3. If a failure can recur, codify it in a skill/workflow instead of relying on memory.
4. If evidence is missing, do not claim success.

## Scope Boundary

Use this skill only for common-sense engineering checks.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## References

- `references/common-sense-checklist.md` — full before/during/after checklist.

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
