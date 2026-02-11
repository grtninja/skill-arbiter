---
name: repo-b-mass-index-ops
description: Run safe bounded mass-index operations for <PRIVATE_REPO_B> connector and bridge service lanes using non-sharded safe-mass-index-core presets. Use when triaging shim routing, service endpoints, or bridge-related source trees.
---

# REPO_B Mass Index Ops

Use this wrapper for `<PRIVATE_REPO_B>` service and connector indexing. It delegates indexing logic to `safe-mass-index-core` with repo-b-specific query intent.

## Workflow

1. Build or refresh a bounded non-sharded index for fast service lookups.
2. Run connector, bridge, and endpoint-adjacent queries.
3. Escalate to `safe-mass-index-core` directly for non-service discovery tasks.

## Scope Boundary

Use this skill when the task is primarily about:

1. Connector/service paths.
2. Bridge/API wiring.
3. Runtime helper scripts around service surfaces.

Do not use this skill for:

1. Very large shard-first repository sweeps (use `repo-c-mass-index-ops`).
2. UI/package-heavy desktop trees (use `repo-d-mass-index-ops`).

## Build Preset

Run from `<PRIVATE_REPO_B>` root:

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
  --exclude-dir logs \
  --exclude-dir artifacts \
  --exclude-dir target \
  --exclude-dir .cache \
  --exclude-dir .codex-index \
  --json-out .codex-index/run.json
```

## Query Presets

Connector-focused scan:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains connector \
  --ext py \
  --limit 200 \
  --format table
```

Bridge and endpoint wiring scan:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains bridge \
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
