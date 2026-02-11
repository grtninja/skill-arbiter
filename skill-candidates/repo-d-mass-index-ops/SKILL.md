---
name: repo-d-mass-index-ops
description: Run safe bounded mass-index operations for <PRIVATE_REPO_D> desktop UI and package workspaces using safe-mass-index-core presets tuned for build-artifact-heavy repos.
---

# REPO_D Mass Index Ops

Use this wrapper for `<PRIVATE_REPO_D>` UI and package indexing workflows with aggressive build-artifact exclusions.

## Workflow

1. Build or refresh a bounded index that excludes frontend/electron build outputs.
2. Query UI component and package workspace paths.
3. Use `safe-mass-index-core` directly for non-UI repository discovery.

## Scope Boundary

Use this skill when the task is primarily about:

1. Desktop renderer/UI source trees.
2. Shared package workspaces.
3. Build-output hygiene and artifact exclusion sanity.

Do not use this skill for:

1. Connector/bridge service routing searches (use `repo-b-mass-index-ops`).
2. Large sharded governance/policy scans (use `repo-c-mass-index-ops`).

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
  --exclude-dir storybook-static \
  --exclude-dir .turbo \
  --exclude-dir out \
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

Renderer UI component sweep:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains components \
  --ext tsx \
  --limit 200 \
  --format table
```

Package workspace sweep:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains packages \
  --lang typescript \
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
