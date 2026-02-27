# REPO_B Presets

Fast incident budget defaults:

1. `--max-files-per-run 9000`
2. `--max-seconds 18`
3. `--max-read-bytes 50331648`

Use these filters to keep queries focused:

1. Service surfaces: `--path-contains service`
2. Connectors: `--path-contains connector`
3. API routes: `--path-contains route --ext py`
4. Config files: `--ext yaml` or `--ext yml`

If build budgets are too tight for the current change window, temporarily raise only one limit at a time:

- `--max-files-per-run`
- `--max-seconds`
- `--max-read-bytes`

Keep `--mode incremental` as the default.
