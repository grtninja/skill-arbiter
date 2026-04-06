# gh-issues Issue Orchestration Playbook

Use this runbook for Phases 1-5 of `gh-issues`.

## 1. Parse and Derive

Parse the argument string after `/gh-issues`.

Required derived values:

- `SOURCE_REPO`
- `PUSH_REPO`
- `FORK_MODE`
- `BASE_BRANCH`

Support:

- `--dry-run`
- `--yes`
- `--reviews-only`
- `--watch`
- `--interval`
- `--cron`
- `--model`
- `--notify-channel`

If `owner/repo` is omitted, derive it from `git remote get-url origin`.

If `--reviews-only` is set, resolve `GH_TOKEN` first and then jump to the review handler runbook.

## 2. Resolve GH_TOKEN

Resolution order:

1. environment
2. `~/.openclaw/openclaw.json`
3. `/data/.clawdbot/openclaw.json`

Canonical API header:

```bash
curl -s \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/..."
```

If auth returns `401` or `403`, stop and report the configured-token failure.

## 3. Fetch Issues

Fetch from:

```bash
https://api.github.com/repos/{SOURCE_REPO}/issues?per_page={limit}&state={state}&...
```

Query parameters may include:

- `labels={label}`
- `assignee={assignee}`
- `milestone={number}` after resolving the user-provided milestone title

Important:

- exclude results containing a `pull_request` key
- in watch mode, exclude issues already in `PROCESSED_ISSUES`

Extract at least:

- issue number
- title
- body
- labels
- assignees
- `html_url`

## 4. Present and Confirm

- show a markdown issue table
- show fork-mode target if `--fork` is active
- stop immediately on `--dry-run`
- auto-process all on `--yes`
- otherwise ask the user for:
  - `all`
  - comma-separated issue numbers
  - `cancel`

In watch mode:

- confirm only on the first poll unless `--yes` is active
- later polls auto-process newly discovered issues

## 5. Pre-flight Checks

Run these before spawning any fix agent:

1. `git status --porcelain`
2. `git rev-parse --abbrev-ref HEAD`
3. remote reachability checks
4. token validity check with `GET /user`
5. open PR check for `fix/issue-{N}`
6. branch-exists check on `PUSH_REPO`
7. claim-file de-duplication

### Claim File

Use:

```bash
CLAIMS_FILE="/data/.clawdbot/gh-issues-claims.json"
```

Behavior:

- create if missing
- remove expired claims older than 2 hours
- skip issues with live claims

## 6. Spawn Fix Agents

Normal mode:

- spawn one sub-agent per confirmed issue
- max concurrency: `8`

Cron mode:

- use a cursor file
- process one eligible issue only
- write `in_progress`
- fire-and-forget

### Cursor File

```bash
CURSOR_FILE="/data/.clawdbot/gh-issues-cursor-{SOURCE_REPO_SLUG}.json"
```

Track:

- `last_processed`
- `in_progress`

## 7. Fix-Agent Prompt Contract

Every issue-fix agent must:

1. ensure `GH_TOKEN` is available
2. assess confidence before implementing
3. branch from `BASE_BRANCH` as `fix/issue-{number}`
4. analyze the codebase and identify the root cause
5. implement the full fix
6. run relevant tests when present
7. commit with a `Fixes {SOURCE_REPO}#{number}` trailer
8. push to the correct remote
9. open a PR through the GitHub REST API
10. report PR URL, changed files, summary, and caveats

### Required Prompt Variables

- `{SOURCE_REPO}`
- `{PUSH_REPO}`
- `{FORK_MODE}`
- `{PUSH_REMOTE}`
- `{BASE_BRANCH}`
- `{number}`
- `{title}`
- `{url}`
- `{labels}`
- `{body}`
- `{notify_channel}`

### Fix-Agent Constraints

- do not use `gh`
- do not force-push
- no unrelated refactors
- no new dependencies without justification
- stop if confidence is below `7/10`
- timeout: `3600s`

## 8. Results Collection

Collect status rows for:

- PR opened
- failed
- timed out
- skipped

Always report:

- issue number
- status
- PR URL if present
- concise notes

If `--notify-channel` is set, send only the final success-summary notification.
