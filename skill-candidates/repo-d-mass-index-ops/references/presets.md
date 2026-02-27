# REPO_D Presets

Build exclusion profile:

1. Keep `.next`, `.vite`, `.turbo`, `storybook-static`, and `out` excluded.
2. Keep generated package output paths excluded unless debugging packaging artifacts.
3. Keep index mode incremental for daily work.

Recommended query patterns:

1. Frontend code: `--ext ts --scope src`
2. UI assets/components: `--path-contains ui`
3. Package boundaries: `--path-contains packages`
4. Build config: `--path-contains config --ext json`

Avoid indexing generated output directories unless explicitly needed for diagnostics.
