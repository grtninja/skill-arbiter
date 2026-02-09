---
name: repo-c-mass-index-ops
description: Run safe bounded mass-index operations for <PRIVATE_REPO_C> using safe-mass-index-core large-repo presets. Use when indexing very large repository trees with shard-first queries.
---

# REPO_C Mass Index Ops

Use this wrapper for large repo-c indexing workflows. It delegates all indexing logic to `safe-mass-index-core`.

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

Scope a single top-level shard:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --scope src \
  --limit 200 \
  --format table
```

Narrow shard + language:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --scope services \
  --lang python \
  --limit 200 \
  --format table
```

## Reference

- `references/presets.md`
