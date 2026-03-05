# CodexBar CLI Notes

`model-usage` expects JSON shaped like `codexbar cost --format json`.

Typical command:

```bash
codexbar cost --format json --provider codex
```

Known provider values in this workflow:

- `codex`
- `claude`

The script also accepts:

- saved JSON file via `--input /path/to/file.json`
- stdin via `--input -`
