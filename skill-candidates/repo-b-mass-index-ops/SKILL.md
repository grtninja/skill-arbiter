---
name: repo-b-mass-index-ops
description: Run safe bounded mass-index operations for <PRIVATE_REPO_B> using safe-mass-index-core presets. Use when indexing connector/service trees in a large shim-style repository.
---

# REPO_B Mass Index Ops

Use this wrapper for repo-b indexing workflows. It delegates all indexing logic to `safe-mass-index-core`.

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
  --exclude-dir target \
  --exclude-dir .cache \
  --exclude-dir .codex-index \
  --json-out .codex-index/run.json
```

## Query Presets

Connector-focused query:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains connector \
  --limit 200 \
  --format table
```

Python service files changed recently:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --ext py \
  --lang python \
  --changed-since-epoch <seconds> \
  --limit 200 \
  --format table
```

## Reference

- `references/presets.md`
