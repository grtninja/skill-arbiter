---
name: repo-b-mass-index-ops
description: Run fast non-sharded mass-index operations for <PRIVATE_REPO_B> service lanes. Use when triaging bridge wiring, thin-waist routes, control-center connectors, and runtime helper scripts where quick endpoint-path discovery is required.
---

# REPO_B Mass Index Ops

Use this wrapper for incident-speed service discovery in `<PRIVATE_REPO_B>`.

## Fast Lane

1. Build or refresh a non-sharded index for rapid endpoint lookups.
2. Pivot on service anchors first: `lighthouse`, `posebridge`, `connector-registry`, `shim-router`, and `control-center`.
3. Escalate to `safe-mass-index-core` only when lane-specific anchors fail to localize the target.

## Repo-B Anchors

Use these anchor paths to keep searches deterministic and lane-specific:

- `apps/mx3-control-center`
- `scripts/restart_headless.ps1`
- `tools/restart_local_apps.py`
- `tools/hybrid_doctor.py`
- `api/mcp/status`
- `api/agent/capabilities`

## Scope Boundary

Use this skill when the task is primarily about:

1. Bridge and connector routing logic.
2. Thin-waist service handlers and model routes.
3. Control-center service integration files.

Do not use this skill for:

1. Governance schema tracing lanes.
2. Desktop renderer or packaging indexing lanes.

## Build Preset (Fast, Non-Sharded)

Run from `<PRIVATE_REPO_B>` root:

Use the standard `safe-mass-index-core` build command with a fast incident budget:

1. `--mode incremental`
2. `--max-files-per-run 9000`
3. `--max-seconds 18`
4. `--max-read-bytes 50331648`

## Query Presets

Bridge and agent route scan:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains bridge \
  --ext py \
  --limit 160 \
  --format table
```

Control-center endpoint scan:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --path-contains control-center \
  --path-contains lighthouse \
  --path-contains route \
  --lang python \
  --limit 160 \
  --format table
```

## Reference

- `references/presets.md`

## Loopback

If a run is still ambiguous, send query args plus `.codex-index/run.json` evidence through `$skill-hub` for deterministic rerouting.
