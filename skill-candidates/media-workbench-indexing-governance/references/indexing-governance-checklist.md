# Media Workbench Indexing Governance Checklist

Use this reference when Media Workbench indexing behavior changes.

## Required Alignment

1. `metadata_only` default posture
2. local-only manifest and catalog storage
3. content-derived indexing remains explicit opt-in
4. operator-facing summaries match actual index scope
5. validation scripts still prove the changed catalog path

## Failure Patterns

- content-derived indexing becomes implied instead of explicit
- indexes or catalogs spill into the private media root
- operator summaries suggest a richer catalog than the repo actually built
- catalog builders and validation scripts drift from the documented indexing posture
