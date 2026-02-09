---
name: starframe-metaranker-contracts
description: Maintain MetaRanker engine behavior and schema compatibility in <STARFRAME_REPO>. Use when modifying scoring weights, ranking/multiplier logic, report serialization, or metaranker_report schema contracts consumed by downstream systems.
---

# STARFRAME MetaRanker Contracts

Use this skill for MetaRanker logic and contract-safe updates.

## Workflow

1. Update `starframe/metaranker.py` with deterministic scoring changes.
2. Validate report serialization against schema expectations.
3. Verify tests covering engine behavior and schema conformance.

## Commands

Run from `<STARFRAME_REPO>` root:

```bash
ruff check .
pytest -q tests/test_metaranker_engine.py tests/test_schema_validation.py
```

Schema alignment target:

- `schemas/metaranker_report.schema.json`

## Contract Notes

- Keep `MetaRankerReport.to_dict()` output stable.
- Preserve `apply_credit(report, base_credit)` multiplier semantics.
- Additive schema evolution preferred over breaking changes.

## Reference

- `references/metaranker-contracts.md`
