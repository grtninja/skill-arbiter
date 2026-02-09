---
name: repo-d-mass-index-ops
description: Run safe bounded mass-index operations for <PRIVATE_REPO_D> using safe-mass-index-core presets. Use when indexing sandbox UI/build-heavy repos while excluding artifact churn.
---

# REPO_D Mass Index Ops

Use this wrapper for repo-d indexing workflows. It delegates all indexing logic to `safe-mass-index-core`.

## Build Preset

Run from `<PRIVATE_REPO_D>` root:

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
  --exclude-dir .next \
  --exclude-dir .vite \
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

UI and package boundaries:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains ui \
  --limit 200 \
  --format table
```

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains packages \
  --limit 200 \
  --format table
```

## Reference

- `references/presets.md`
