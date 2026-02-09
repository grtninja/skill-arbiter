# Validation Contract

`tools/local_bridge_validate.py` enforces strict local-response gates before any bridge output can influence final agent responses.

## Inputs

- Bridge task response payload (JSON object).
- Candidate path list from bounded index queries.
- `repo_root` path.
- Allowed root list.
- Thresholds:
  - `confidence_min` (default `0.85`)
  - `evidence_min` (default `2`)
  - `coverage_min` (default `0.70`)
  - `max_hints` (default `12`)

## Pass Requirements

Validation passes only when all checks pass:

1. Structured payload yields at least one normalized hint.
2. Every cited path resolves inside an allowed root.
3. At least `evidence_min` hints include non-empty evidence.
4. Coverage ratio across candidate paths is at least `coverage_min`.
5. Aggregate confidence score is at least `confidence_min`.

## Failure Behavior

When any gate fails:

- `status` is `validation_failed`.
- `reason_codes` include one or more of:
  - `schema_invalid`
  - `unauthorized_path`
  - `low_confidence`
  - `insufficient_evidence`
- No cloud fallback is attempted.

## Normalized Hint Shape

Each emitted `guidance_hints` entry contains:

- `path`: repository-relative POSIX path
- `finding`: concise finding statement
- `evidence`: array of evidence strings
- `confidence`: float in `[0.0, 1.0]`
- `priority`: `high`, `medium`, or `low`

Hints are sorted deterministically and truncated to `max_hints`.
