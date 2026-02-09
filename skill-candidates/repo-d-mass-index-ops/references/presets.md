# REPO_D Presets

Recommended query patterns:

1. Frontend code: `--ext ts --scope src`
2. UI assets/components: `--path-contains ui`
3. Package boundaries: `--path-contains packages`
4. Build config: `--path-contains config --ext json`

Avoid indexing generated output directories unless explicitly needed for diagnostics.
