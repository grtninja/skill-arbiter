# BOUNDARIES.md

## Scope
`skill-arbiter` is the skill governance and admission-control lane.

## Allowed Lane
- Skill discovery, admission tests, quarantine, reliability scoring, and churn/risk evidence.
- Policy enforcement for SAFE/SHARP/LIVE skill classes.
- Local governance artifacts (trust ledger, blast-radius reports, admission traces).

## Forbidden Lane
- Direct control of runtime inference, persona engines, or hardware scheduling.
- Acting as an autonomous application orchestrator for VRM/STARFRAME/MX3 execution.
- Secret material ingestion/export and private host detail publication.

## Cross-Repo Boundary
- This repo may evaluate policy compliance across repos through documented checks.
- This repo must not own or mutate runtime behavior in:
  - `<PRIVATE_REPO_A>`
  - `<PRIVATE_REPO_B>`
  - `<PRIVATE_REPO_C>`
  - `<PRIVATE_REPO_D>`
  - `<PRIVATE_REPO_E>`
- Runtime repos remain source-of-truth for execution behavior; arbiter remains governance-only.

## Safety Boundary
- Skill installs are treated as executable trust boundaries, not passive content.
- Default posture is fail-closed: deny/disable/quarantine on policy uncertainty.
- Evidence-driven admissions are required before enabling new or changed skills.

