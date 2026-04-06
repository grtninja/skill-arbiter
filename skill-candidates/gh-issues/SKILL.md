---
name: gh-issues
description: "Fetch GitHub issues, spawn sub-agents to implement fixes and open PRs, then monitor and address PR review comments. Usage: /gh-issues [owner/repo] [--label bug] [--limit 5] [--milestone v1.0] [--assignee @me] [--fork user/repo] [--watch] [--interval 5] [--reviews-only] [--cron] [--dry-run] [--model glm-5] [--notify-channel -1002381931352]"
---

# gh-issues

Use this skill to run the issue-to-PR automation lane for GitHub repositories.

This skill is now segmented into a lean router plus detailed runbooks in `references/` so the top-level skill stays readable while preserving the full orchestration contract.

## Use This Skill When

- the request is to fetch issues from a GitHub repo and auto-process them
- the request is to spawn bounded sub-agents that fix issues and open PRs
- the request is to monitor `fix/issue-*` pull requests for review feedback
- the request needs cron-safe issue or review polling with claims/cursor tracking

## Route Elsewhere When

- the user wants general GitHub orientation or repo context only: use `$github`
- the user wants one specific PR's review comments handled manually: prefer `$gh-address-comments`
- the user wants failing GitHub Actions diagnosed: prefer `$gh-fix-ci`
- the request is broader than one GitHub issue-processing lane: route through `$skill-hub`

## Non-Negotiable Contract

1. Do not use the `gh` CLI. This skill uses `curl` plus the GitHub REST API only.
2. Resolve `GH_TOKEN` before any GitHub API call:
   - environment first
   - `~/.openclaw/openclaw.json`
   - `/data/.clawdbot/openclaw.json`
3. Filter GitHub Issues API results to exclude pull requests.
4. Respect `--dry-run`, `--yes`, `--reviews-only`, `--watch`, `--cron`, `--fork`, and `--notify-channel`.
5. Never duplicate live work:
   - skip issues with open PRs
   - skip issues with in-progress `fix/issue-*` branches on the push repo
   - skip issues already claimed in the claims file
6. Spawn bounded sub-agents only after pre-flight checks pass.
7. Keep sub-agent concurrency at `8` max in normal mode.
8. Preserve watch-mode state with minimal retained context only.

## Supported Flags

| Flag | Default | Purpose |
| --- | --- | --- |
| `owner/repo` | detect from git remote | Source repo whose issues are fetched |
| `--label` | none | Filter by label |
| `--limit` | `10` | Issues per poll |
| `--milestone` | none | Milestone title to resolve and filter |
| `--assignee` | none | Assignee filter (`@me` supported) |
| `--state` | `open` | Issue state |
| `--fork` | none | Push branches to fork, open PRs back to source repo |
| `--watch` | `false` | Poll for new issues and review comments |
| `--interval` | `5` | Minutes between polls |
| `--dry-run` | `false` | Fetch and show only |
| `--yes` | `false` | Skip confirmation |
| `--reviews-only` | `false` | Skip issue processing, review PRs only |
| `--cron` | `false` | Cron-safe fire-and-forget mode |
| `--model` | none | Override model for spawned sub-agents |
| `--notify-channel` | none | Telegram channel for final summary |

## Workflow

1. Parse arguments and derive:
   - `SOURCE_REPO`
   - `PUSH_REPO`
   - `FORK_MODE`
2. Resolve `GH_TOKEN` and fetch issues or review targets using the REST API.
3. Present the candidate issue/PR set unless `--yes` or cron behavior skips confirmation.
4. Run pre-flight checks:
   - dirty working tree warning
   - base branch detection
   - remote reachability
   - token validity
   - existing PR detection
   - existing branch detection on the push repo
   - claim-file de-duplication
5. Spawn bounded issue-fix sub-agents in parallel, or one-at-a-time in cron mode with cursor tracking.
6. Collect results:
   - PR opened
   - failed
   - timed out
   - skipped
7. Run the review handler:
   - discover actionable comments on open `fix/issue-*` PRs
   - spawn review-fix sub-agents
   - reply to addressed comments
8. If `--watch` is active, retain only watch-safe state and loop.

## Pre-flight Requirements

- warn on dirty working tree before branching
- record `BASE_BRANCH`
- verify the source remote is reachable
- in fork mode, ensure the `fork` remote exists or add it with token auth
- validate `GH_TOKEN` with `GET /user`
- skip issues with existing open PRs
- skip issues whose `fix/issue-*` branches already exist on the push repo
- skip unexpired issue claims

Detailed commands, API endpoints, and file-state rules live in:

- `references/issue-orchestration-playbook.md`

## Sub-agent Contracts

There are two spawned sub-agent lanes:

1. Issue-fix agents
   - one issue per agent
   - branch from `BASE_BRANCH`
   - implement complete synchronized fix
   - test when possible
   - commit, push, and open PR through the GitHub REST API
2. Review-fix agents
   - one PR per agent
   - fetch and address actionable review comments
   - push updates and reply to comment threads

Shared rules:

- `runTimeoutSeconds: 3600`
- `cleanup: "keep"`
- pass `--model` through when provided
- do not force-push
- do not make unrelated changes
- stop and report when confidence is too low

Detailed prompt templates and reply behavior live in:

- `references/issue-orchestration-playbook.md`
- `references/review-handler-playbook.md`

## State Files

- Claims file: `/data/.clawdbot/gh-issues-claims.json`
- Cron cursor file: `/data/.clawdbot/gh-issues-cursor-{SOURCE_REPO_SLUG}.json`

Use these files to prevent duplicate work across cron runs, watch mode, and interactive sessions.

## Results Contract

Always report a deterministic summary table covering:

- issue or PR number
- status
- PR URL if opened
- notes or blockers

If `--notify-channel` is set, send only the final PR summary to Telegram.

## Watch Mode Contract

Between polls retain only:

- `PROCESSED_ISSUES`
- `ADDRESSED_COMMENTS`
- `OPEN_PRS`
- cumulative result lines
- parsed arguments and repo/base-branch state

Do not retain issue bodies, comment bodies, transcripts, or code analysis between poll cycles.

## Guardrails

- use trusted local tools only
- never print secrets or tokens in chat output
- keep outputs deterministic and reviewable
- skip unclear or too-large issues instead of guessing
- preserve fork/source-repo separation correctly in fork mode

## References

- `references/issue-orchestration-playbook.md`
- `references/review-handler-playbook.md`
