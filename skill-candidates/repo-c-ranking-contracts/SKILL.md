---
name: repo-c-ranking-contracts
description: Maintain ranking engine behavior and schema compatibility in <PRIVATE_REPO_C>. Use when modifying scoring weights, ranking/multiplier logic, report serialization, or `ranking_report` schema contracts consumed by downstream systems.
---

# Repo C Ranking Engine Contracts

Use this skill for Ranking Engine logic and contract-safe updates.

## Workflow

1. Update `repo_c/ranking_engine.py` with deterministic scoring changes.
2. Validate report serialization against schema expectations.
3. Verify tests covering engine behavior and schema conformance.

## Scope Boundary

Use this skill for ranking/scoring behavior and `ranking_report` contract stability.

Do not use this skill for:

1. Policy manifest/schema validation CLI lanes (use `repo-c-policy-schema-gate`).
2. NDJSON trace packet and guardian stream checks (use `repo-c-trace-ndjson-validate`).
3. High-level cross-repo boundary governance reviews (use `repo-c-boundary-governance`).

## Commands

Run from `<PRIVATE_REPO_C>` root:

```bash
ruff check .
pytest -q tests/test_ranking_engine.py tests/test_schema_validation.py
```

Schema alignment target:

- `schemas/ranking_report.schema.json`

## Contract Notes

- Keep `RankingEngineReport.to_dict()` output stable.
- Preserve `apply_credit(report, base_credit)` multiplier semantics.
- Additive schema evolution preferred over breaking changes.

## Reference

- `references/ranking-contracts.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
