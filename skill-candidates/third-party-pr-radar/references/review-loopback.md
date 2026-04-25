# Review Loopback

Use the PC Control hub on `http://127.0.0.1:8890` as the Codex review loopback surface.

## Health Checks

- `GET /v1/agent-fabric/connectors/codex/status`
- `GET /v1/agent-fabric/connectors/continue/status`
- `GET /v1/agent-fabric/evidence/code-review-ledger`
- `GET /v1/agent-fabric/evidence/contribution-ledger`

Before using review evidence on a live PR lane, also capture:

- current head SHA
- current check state on that head
- whether the visible red is `active_red`, `stale_red`, `pending`, or `clean`

## Local Codex Session Prepare

Endpoint:

- `POST /v1/agent-fabric/plugins/local-codex-harness/session/prepare`

Use the exact request shape. `actor` and `intent` are mandatory for reliable behavior in the local harness route.

Minimal request body:

```json
{
  "actor": "codex",
  "intent": "Prepare governed local context for third-party PR scouting or review.",
  "target_repo_or_service": "owner/repo",
  "working_dir": "<PRIVATE_GITHUB_ROOT>\\repo",
  "task_kind": "third_party_pr_radar",
  "attachment_paths": [],
  "asks_browser": false,
  "asks_web_search": false,
  "allow_write": false,
  "preferred_lane": "codex"
}
```

## Queued Review Coder

Preferred endpoint:

- `POST /v1/agent-fabric/code-review-runs`

Poll:

- `GET /v1/agent-fabric/code-review-runs/{run_id}`

Use `target_repo_or_service` and `working_dir`.
Do not substitute `repo` and `repo_path` here, or the queued record can silently degrade into a generic `repo` placeholder instead of the real workspace you meant to review.

Minimal request body:

```json
{
  "actor": "codex",
  "instruction": "Review the current diff before PR action.",
  "target_repo_or_service": "owner/repo",
  "working_dir": "<PRIVATE_GITHUB_ROOT>\\repo",
  "reasoning_effort": "high",
  "max_files": 12,
  "include_patch_excerpt": true,
  "wait_for_completion": false,
  "dry_run": false
}
```

## Contribution Ledger Upsert

Endpoint:

- `POST /v1/agent-fabric/contributions`

Minimal request body:

```json
{
  "actor": "codex",
  "repo": "owner/repo",
  "repo_path": "<PRIVATE_GITHUB_ROOT>\\repo",
  "summary": "Track the third-party lane and its review artifacts.",
  "status": "in_progress",
  "scope": ["third_party_pr", "white_hat"],
  "security_skills": ["white-hat"],
  "artifacts": [],
  "pr_urls": [],
  "notes": []
}
```

If `codex/status` is healthy but `code-review-runs` times out or stalls, record that as degraded reviewer evidence rather than pretending the review passed.

## CI-Derived Narrow Validation

Use the target repo's own workflow and script layout to decide the narrow rerun.

- If the repo exposes changed-scope or docs-only routing, mirror that first.
- If the repo exposes changed-extension or changed-package routing, use that before broad suite reruns.
- Record the narrow validation commands alongside the review run so later PR triage is reproducible.

OpenClaw reference pattern:

- `check` -> `pnpm check` plus `pnpm build:strict-smoke`
- `checks-fast-contracts-protocol` -> `pnpm test:contracts` plus `pnpm protocol:check`
- `checks-node-extensions-shard-*` -> exact extension or paired extension/core rerun, not automatic whole-suite rerun
- `gateway-watch-regression` -> dedicated harness rerun only when the touched surface owns that failure

If the red is stale on a superseded head, capture the lane mapping anyway and mark the CI note as `stale_red` instead of forcing a speculative fix.
