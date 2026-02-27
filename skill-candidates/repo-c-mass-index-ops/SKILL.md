---
name: repo-c-mass-index-ops
description: Run shard-first mass-index operations for <PRIVATE_REPO_C> governance lanes. Use when scanning policy schemas, ranking/trace contracts, and trust-layer boundaries in very large trees where scope partitioning is required.
---

# REPO_C Mass Index Ops

Use this wrapper for governance-heavy discovery in very large `<PRIVATE_REPO_C>` repositories.

## Governance Scan Sequence

1. Build or refresh sharded index data with bounded budgets.
2. Query policy and trust envelopes first, then narrow to contract files.
3. Escalate to `safe-mass-index-core` only for custom envelopes outside governance lanes.

## Repo-C Anchors

Prioritize these governance contract anchors during triage:

- `policies/repo-c_policy.yaml`
- `policies/device_policy.json`
- `schemas/ranking_report.schema.json`
- `tools/trace_validate.py`
- `repo_c_trace`
- `trust_anchor`
- `emotion_ttl`

## Scope Boundary

Use this skill when the task is primarily about:

1. Policy and schema contract surfaces.
2. Trace/ranking packet contracts and validation tools.
3. Cross-domain governance boundaries.

Do not use this skill for:

1. Runtime connector incident scans.
2. Electron/UI package scans.

## Build Preset (Sharded Governance)

Run from `<PRIVATE_REPO_C>` root:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_build.py" \
  --repo-root . \
  --index-dir .codex-index \
  --mode incremental \
  --max-files-per-run 14000 \
  --max-seconds 30 \
  --max-read-bytes 67108864 \
  --sharded \
  --json-out .codex-index/run.json
```

## Query Presets (Governance First)

Policy and schema scope:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --scope policy \
  --lang json \
  --limit 220 \
  --format table
```

Trace and ranking contract scope:

```bash
python3 "$CODEX_HOME/skills/safe-mass-index-core/scripts/index_query.py" \
  --index-dir .codex-index \
  --scope trace \
  --path-contains trust_anchor \
  --path-contains contract \
  --lang python \
  --limit 220 \
  --format table
```

## Reference

- `references/presets.md`

## Loopback

If a run is still ambiguous, pass shard settings, scope filters, and `.codex-index/run.json` evidence to `$skill-hub` for deterministic rerouting.
