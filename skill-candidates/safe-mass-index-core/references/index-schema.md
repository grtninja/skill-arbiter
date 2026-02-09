# Index Artifact Schema

## Manifest

Path: `.codex-index/manifest.json`

Fields:

- `schema_version`: integer schema version
- `repo_root`: absolute repo root used for index build
- `generated_at_epoch`: unix epoch seconds
- `run_config`: build options and budgets
- `counters`: file/read/skip/update counters
- `storage`:
  - `sharded`: boolean
  - `files_path`: `files.jsonl` or `null`
  - `shard_map`: object `{top_level: "shards/<name>.jsonl"}`

## State

Path: `.codex-index/state.json`

Fields:

- `schema_version`
- `repo_root`
- `updated_at_epoch`
- `entries` object keyed by relative path:
  - `fingerprint`: `[size, mtime_ns, dev, ino]`
  - `record`: file metadata record

Corrupt/invalid state triggers safe incremental fallback rebuild.

## File Listing

Non-sharded:

- `.codex-index/files.jsonl`

Sharded:

- `.codex-index/shards/<top-level>.jsonl`

Each line is one JSON record:

```json
{
  "path": "relative/path.ext",
  "size": 12345,
  "mtime_ns": 1739100000000000000,
  "ext": ".ext",
  "lang": "python",
  "text_like": true,
  "top_level": "src"
}
```

No file body content is indexed in v1.

## Run Report

Path: `.codex-index/run.json`

Fields:

- `status`: `ok` or `partial`
- `stop_reason`: `completed` or budget stop marker
- `duration_seconds`
- `fallback_rebuild` + `fallback_reason`
- `budgets` and `usage`
- `counters`
- `storage` summary
