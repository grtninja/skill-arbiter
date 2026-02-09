---
name: safe-mass-index-core
description: Build and query bounded metadata-only repository indexes without rg process churn. Use when working in very large repos and you need deterministic file discovery by path, extension, language, scope, or freshness.
---

# Safe Mass Index Core

Use this skill to index large repositories safely without `rg` subprocess churn.

## Policy

1. Do not use `rg`/`rg.exe` for mass indexing.
2. Use only local filesystem metadata and bounded lightweight probing.
3. Keep runs bounded with file/time/read-byte budgets.

## Build Command

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_build.py" \
  --repo-root <path> \
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
  --exclude-dir dist \
  --exclude-dir build \
  --exclude-dir target \
  --exclude-dir .cache \
  --exclude-dir .codex-index \
  --json-out .codex-index/run.json
```

For very large repos, enable sharded storage:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_build.py" \
  --repo-root <path> \
  --index-dir .codex-index \
  --mode incremental \
  --max-files-per-run 12000 \
  --max-seconds 25 \
  --max-read-bytes 67108864 \
  --sharded
```

## Query Command

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains <text> \
  --ext <extension> \
  --lang <language_tag> \
  --min-size <bytes> \
  --max-size <bytes> \
  --changed-since-epoch <seconds> \
  --scope <top_level_dir_or_all> \
  --limit 200 \
  --format table
```

## Outputs

- `.codex-index/manifest.json`
- `.codex-index/state.json`
- `.codex-index/files.jsonl` (non-sharded)
- `.codex-index/shards/*.jsonl` (sharded)
- `.codex-index/run.json`

## Reference

- `references/index-schema.md`
