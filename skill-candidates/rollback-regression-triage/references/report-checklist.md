# Rollback Regression Triage Checklist

Use this checklist to keep rollback forensics deterministic.

## Inputs

1. Repo path
2. Last-known-good commit or bounded date window
3. Compare ref
4. Focus paths
5. User-stated desired outcomes
6. Relevant GitHub PR numbers or CI run IDs when available

## Mandatory outputs

1. Bug fixed by rollback
   - commit
   - file
   - why rollback fixed it
2. Remaining culprit changes
   - commit
   - file
   - why still harmful
3. Desired vs actual mismatches
   - expected behavior
   - observed code behavior
4. GitHub proof
   - local only
   - pushed to branch
   - merged to main
   - relevant PR timing if checked
5. GitHub supporting evidence
   - exact PR(s) tied to the suspect branch
   - exact failed/succeeded run(s) tied to the suspect branch
   - whether that evidence is causal or corroborating only

## Review order

1. Launcher or startup contract changes
2. Runtime mode or policy gating changes
3. UI/operator-surface cuts
4. Polling or degradation behavior
5. PR/CI evidence that narrows the suspect window
6. Docs-only drift

## Guardrails

- Do not guess the good anchor.
- Do not treat commit date as merge date.
- Do not claim a change is local-only until remote containment is checked.
- Do not bury the rollback-fixed bug under lower-severity UI or docs drift.
- Do not treat a failed PR contract or CI notification as the bug without tying it back to the changed hunk.
