---
name: repo-d-mass-index-ops
description: Run UI-and-packaging mass-index operations for <PRIVATE_REPO_D> workspace trees. Use when scanning renderer components, Electron startup files, workspace packages, and packaging scripts while aggressively excluding generated build artifacts.
---

# REPO_D Mass Index Ops

Use this wrapper for desktop UI and packaging lanes in `<PRIVATE_REPO_D>`.

## UI/Packaging Scan Sequence

1. Build or refresh an index with frontend/build exclusions.
2. Query renderer, preload, and package workspace paths first.
3. Escalate to `safe-mass-index-core` only for non-desktop discovery lanes.

## Repo-D Anchors

Use these anchors to keep the query lane tied to desktop packaging behavior:

- `renderer`
- `preload`
- `windowBounds`
- `windowManager`
- `electron/main`
- `packages/desktop-shell`
- `storybook-static`
- `app.asar`

## Scope Boundary

Use this skill when the task is primarily about:

1. Desktop renderer/UI source trees.
2. Electron main/preload and startup sequencing files.
3. Packaging and distribution workspace scripts.

Do not use this skill for:

1. Service/bridge route triage.
2. Sharded governance contract scans.

## Build Preset

Run from `<PRIVATE_REPO_D>` root:

Use the standard `safe-mass-index-core` build command with the repo-d exclusion profile in `references/presets.md`.
Keep frontend/Electron artifacts excluded by default.

## Query Presets

Renderer and component sweep:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains renderer \
  --path-contains ui \
  --ext tsx \
  --limit 180 \
  --format table
```

Packaging workspace sweep:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains packages \
  --path-contains build \
  --lang typescript \
  --limit 180 \
  --format table
```

## Reference

- `references/presets.md`

## Loopback

If results stay ambiguous, send filter args plus `.codex-index/run.json` to `$skill-hub` for deterministic rerouting.
