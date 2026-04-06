# gh-issues Review Handler Playbook

Use this runbook for Phase 6 and watch-mode review handling.

## 1. When the Review Handler Runs

Run this phase:

- after fix-agent results are collected
- when `--reviews-only` is set
- on each watch-mode poll after issue processing
- in cron review mode when `--cron --reviews-only` is set

## 2. Discover PRs

If coming from issue-processing results, reuse the newly opened PR list.

Otherwise fetch open PRs:

```bash
curl -s \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/{SOURCE_REPO}/pulls?state=open&per_page=100"
```

Only keep PRs whose `head.ref` starts with `fix/issue-`.

## 3. Fetch Review Sources

For each PR, fetch:

- pull-request reviews
- pull-request review comments
- issue comments on the PR
- PR body for embedded review content

Embedded reviews may include bot-generated summaries such as Greptile markers in the PR body.

## 4. Actionability Rules

Treat as actionable:

- `CHANGES_REQUESTED` reviews
- comments asking for a concrete change
- inline review comments pointing to a code problem
- embedded reviews identifying breakage, missing tests, or specific concerns

Treat as non-actionable:

- approvals and pure `LGTM`
- informational bot comments
- already-addressed comments
- reviews with no concrete requested change

Always exclude comments authored by the bot account itself.

Build `actionable_comments` with:

- `id`
- `user`
- `body`
- `path`
- `line`
- `diff_hunk`
- `source`

## 5. Present Review Work

Display a table of PRs with pending actionable comments.

If `--yes` is not set and this is not an automatic watch poll, ask the user which PRs to address:

- `all`
- comma-separated PR numbers
- `skip`

## 6. Review-Fix Agent Contract

Spawn one sub-agent per PR with actionable comments.

Every review-fix agent must:

1. ensure `GH_TOKEN` is available
2. fetch and check out the PR branch
3. read all actionable comments
4. group feedback by file and intent
5. implement requested changes
6. run relevant tests
7. commit changes in one review-response commit
8. push the branch
9. reply to each addressed comment thread
10. report counts, commit SHA, changed files, and manual follow-up items

### Required Variables

- `{SOURCE_REPO}`
- `{PUSH_REPO}`
- `{FORK_MODE}`
- `{PUSH_REMOTE}`
- `{pr_number}`
- `{pr_url}`
- `{branch_name}`
- `{json_array_of_actionable_comments}`

### Constraints

- only modify files relevant to the comments
- no unrelated changes
- no force-push
- use REST API replies, not `gh`
- timeout: `3600s`

## 7. Cron Review Mode

When `--cron --reviews-only` is set:

1. resolve `GH_TOKEN`
2. discover open `fix/issue-*` PRs
3. fetch review sources
4. analyze actionability
5. spawn one review-fix sub-agent for the first actionable PR
6. report spawn status and exit immediately

If no actionable comments exist, report that and exit.

## 8. Review Results

After review-fix agents complete, report:

- PR number
- comments addressed
- comments skipped
- commit SHA
- status

Add addressed comment IDs to `ADDRESSED_COMMENTS` so watch mode does not reprocess them.

## 9. Watch Mode

Between polls retain only:

- `PROCESSED_ISSUES`
- `ADDRESSED_COMMENTS`
- `OPEN_PRS`
- cumulative summaries
- parsed arguments and repo/base-branch state

Do not retain issue bodies, review bodies, transcripts, or code analysis.

Loop behavior:

1. report next poll interval
2. sleep
3. fetch new issues
4. run fix processing if needed
5. run review handling
6. if no new issue or review work exists, report that and continue polling
