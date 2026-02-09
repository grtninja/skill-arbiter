---
name: repo-c-policy-schema-gate
description: Validate Repo C policy files and schema contracts in <PRIVATE_REPO_C>. Use when editing policy manifests, schema files, policy validation CLI logic, or tests that rely on schema conformance.
---

# Repo C Policy Schema Gate

Use this skill to enforce policy/schema correctness.

## Workflow

1. Validate policy files with the CLI.
2. Confirm schema updates remain backward-compatible for consumers.
3. Run lint/tests for affected policy and schema code.

## Core Commands

Run from `<PRIVATE_REPO_C>` root:

```bash
python -m tools.policy_validate policies/repo-c_policy.yaml
python -m tools.policy_validate policies/device_policy.json
ruff check .
pytest -q
```

## Output Requirements

- No policy validation failures.
- Any schema change includes matching test updates.
- Policy docs reflect new required/optional fields.

## Reference

- `references/policy-files.md`
