# Ledger Schema

The dated-version tracking ledger is JSONL. Each line is one independent JSON object.

Default path:

```text
%USERPROFILE%\.codex\workstreams\dated-version-context-ledger.jsonl
```

## Common Fields

- `schema_version`: integer, currently `1`
- `record_id`: stable string ID
- `kind`: `version_assumption`, `dependency_assumption`, `context_request`, `context_fact`, or `stale_check`
- `recorded_at`: ISO 8601 timestamp
- `subject`: short subject
- `claim`: exact operational claim
- `source`: `user`, `current_thread`, `official_docs_web`, `local_config`, `local_process`, `repo`, `memory`, `transcript`, or a combined value
- `source_time`: ISO 8601 timestamp for when the source event occurred
- `status`: `active`, `unverified`, `stale`, `superseded`, or `rejected`
- `confidence`: `high`, `medium`, or `low`
- `freshness_rule`: how future agents decide whether to refresh
- `notes`: optional short notes

## Version And Dependency Fields

- `effective_date`: date the version/dependency assumption became true or was claimed true
- `verified_date`: date the claim was verified
- `evidence`: array of official URLs, local paths, commands, or transcript IDs
- `stale_if`: array of phrases or conditions that would make the claim unsafe
- `refresh_after`: date/time after which the claim must be rechecked before use
- `expires_at`: optional date/time when the claim must not be used without revalidation

## Past Context Fields

- `requested_at`: ISO 8601 timestamp for the user request or source event
- `resolved_time_reference`: object with `raw`, `resolved_start`, and `resolved_end` when a phrase like "last Tuesday" was used
- `valid_until`: optional date/time or rule string
- `supersedes`: optional record ID replaced by this record

## Status Rules

- `active`: usable now, subject to refresh rules
- `unverified`: found but not yet proven current
- `stale`: contradicted by newer evidence or past refresh/expiry
- `superseded`: replaced by a newer entry
- `rejected`: known wrong or unsafe

Never delete stale entries just to make validation pass. Add a newer entry that supersedes them.
