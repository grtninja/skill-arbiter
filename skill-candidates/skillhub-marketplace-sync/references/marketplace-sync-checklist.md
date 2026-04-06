# SkillHub Marketplace Sync Checklist

Use this reference when refreshing SkillHub discovery artifacts.

## Required Surfaces

1. shortlist query set
2. source ledger
3. alignment matrix
4. skill catalog entries tied to marketplace discovery
5. evidence payload under `evidence/`

## Failure Patterns

- alignment matrix refreshed without the ledger
- source posture changes but promotion decision text stays stale
- uncovered destination lanes disappear from the matrix without repo-owned replacements
- fetched temp paths or private machine details leak into generated references
