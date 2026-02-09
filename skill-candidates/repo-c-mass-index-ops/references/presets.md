# REPO_C Large-Repo Presets

Default profile for large repositories:

1. Always build with `--sharded`.
2. Keep `--mode incremental` as baseline.
3. Query with `--scope <top-level>` before full-repo scans.
4. Use `--path-contains` + `--lang` together for fastest narrowing.

When the run is marked partial in `.codex-index/run.json`, re-run with the same settings before broad queries.
