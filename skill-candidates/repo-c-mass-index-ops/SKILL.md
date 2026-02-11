---
name: repo-c-mass-index-ops
description: Run safe bounded mass-index operations for <PRIVATE_REPO_C> policy, trace, and governance lanes using sharded safe-mass-index-core presets. Use when indexing very large repository trees with scope-first shard queries.
---

# REPO_C Mass Index Ops

Use this wrapper for very large `<PRIVATE_REPO_C>` trees where scope-first sharded search is required.

## Workflow

1. Build or refresh a sharded index with bounded budgets.
2. Query by top-level scope first (`policy`, `trace`, `services`, `schemas`), then narrow.
3. Escalate to `safe-mass-index-core` for one-off custom envelopes.

## Scope Boundary

Use this skill when the task is primarily about:

1. Policy/schema contracts.
2. Trace or telemetry packet surfaces.
3. Multi-domain governance trees in a very large repo.

Do not use this skill for:

1. Connector/bridge operational searches (use `repo-b-mass-index-ops`).
2. UI/package-centric desktop trees (use `repo-d-mass-index-ops`).

## Build Preset (Sharded Default)

Run from `<PRIVATE_REPO_C>` root:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_build.py" \
  --repo-root . \
  --index-dir .codex-index \
  --mode incremental \
  --max-files-per-run 12000 \
  --max-seconds 25 \
  --max-read-bytes 67108864 \
  --exclude-dir .git \
  --exclude-dir node_modules \
  --exclude-dir .venv \
  --exclude-dir venv \
  --exclude-dir __pycache__ \
  --exclude-dir build \
  --exclude-dir dist \
  --exclude-dir target \
  --exclude-dir .cache \
  --exclude-dir .codex-index \
  --sharded \
  --json-out .codex-index/run.json
```

## Query Presets (Scope First)

Policy/schema shard focus:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --scope policy \
  --lang json \
  --limit 200 \
  --format table
```

Trace/governance shard focus:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --scope trace \
  --lang python \
  --limit 200 \
  --format table
```

## Reference

- `references/presets.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
