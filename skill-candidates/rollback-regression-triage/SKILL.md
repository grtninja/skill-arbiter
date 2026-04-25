---
name: rollback-regression-triage
description: Investigate a repo rollback or last-known-good restore to find the real regression culprit, rank findings by importance, compare desired outcomes against actual outcomes, and prove whether the bad commits reached GitHub branches or main. Use when a rollback fixes part of a bug, when the user asks what change broke behavior, or when push-status proof matters before any further revert or repair.
---

# Rollback Regression Triage

Use this skill when a rollback improved behavior but did not answer the harder questions:

- what exact change caused the regression,
- which parts of the bug were fixed by the rollback,
- what still mismatches the user's intended outcome,
- whether the bad line ever reached GitHub,
- and whether PR or CI evidence narrowed the culprit window.

## Workflow

1. Lock the contract before reading diffs.
   - Capture the user's desired outcomes in plain language.
   - Separate must-keep surfaces from must-remove behavior.
   - Identify the scope repo and the narrow files or subsystems most likely involved.
2. Prove the last-known-good anchor.
   - Prefer an explicit commit, tag, or quoted user timestamp.
   - If the anchor came from chat history or operator notes, convert it into a concrete commit or bounded date window before blaming later commits.
3. Generate post-anchor commit evidence.
   - Use `scripts/rollback_regression_triage.py` to list commits after the good anchor, diff stats, and remote containment.
   - Narrow to the touched paths that match the broken surface.
4. Triage in this order:
   - bug fixed by rollback,
   - remaining culprit commits not yet fixed,
   - desired-vs-actual mismatches,
   - GitHub exposure status.
5. Inspect the highest-suspicion commits directly.
   - Use `git show --stat` first.
   - Then inspect the exact hunks that changed launcher defaults, UI/operator surfaces, polling, or startup behavior.
6. Prove GitHub exposure.
   - Distinguish `pushed to a branch` from `merged to main`.
   - Use remote containment first.
   - Use `gh pr view` only when PR timing or merge timing matters.
7. Capture GitHub evidence when the branch history alone is not enough.
   - Pull the exact PR(s) and failed run(s) tied to the suspect branch window.
   - Treat notification noise as supporting evidence, not root-cause proof.
   - If a repo-scoped GitHub MCP lane exists, use that before broad manual GitHub spelunking.

## Canonical Command

Run from `<PRIVATE_REPO_ROOT>\skill-candidates\rollback-regression-triage` or call with an absolute path:

```bash
python scripts/rollback_regression_triage.py \
  --repo G:\GitHub\<PRIVATE_REPO_B> \
  --good-commit 677243055bc46cec655429c800c5ec3b1fa02f70 \
  --compare-ref origin/main \
  --focus-path scripts/Start-ControlCenter.ps1 \
  --focus-path tools/restart_local_apps.py \
  --focus-path apps/mx3-control-center/web/src \
  --gh-pr 237 \
  --gh-pr 239 \
  --gh-pr 240 \
  --gh-run 24635531607 \
  --gh-run 24634633074 \
  --json-out %USERPROFILE%\.codex\workstreams\rollback-triage.json
```

## Report Shape

Every report must be ordered and explicit:

1. `P0` bug fixed by rollback
   - exact commit or commit cluster
   - exact files
   - why the rollback fixed this bug
2. `P1+` remaining culprit changes
   - UI cuts
   - startup or polling regressions
   - contract drift
3. Desired vs actual
   - what the user asked for
   - what the changed code actually did
4. GitHub status
   - local only
   - pushed to branch
   - merged to main
5. GitHub supporting evidence
   - PR number and timing when relevant
   - failed/succeeded CI runs on the same branch window
   - whether the failure was causal or only corroborating

Use the checklist in `references/report-checklist.md`.

## GitHub Proof Rules

- `git for-each-ref refs/remotes --contains <commit>` is the first proof surface.
- If a commit is contained by a remote branch, it reached GitHub.
- If timing matters, use `gh pr view <number> --json ...` to separate:
  - commit authored time,
  - PR created time,
  - PR merged time.
- When CI or notification evidence is relevant, use `gh run view <id> --json ...` or equivalent repo-scoped GitHub MCP evidence.
- CI failures are supporting evidence only until their branch, head SHA, and failing surface are tied back to the suspect diff.
- Never flatten `pushed yesterday` and `merged today` into one claim.

## Scope Boundary

Use this skill for rollback and culprit forensics only.

Do not use it for:

1. Performing the actual revert.
2. Editing the target repo unless the user separately asks for the fix.
3. Writing push-ready or release docs as the primary task.

## Resources

- Reporting checklist: `references/report-checklist.md`
- Evidence script: `scripts/rollback_regression_triage.py`

## Loopback

If the anchor is still ambiguous or the evidence does not isolate a culprit:

1. Stop claiming certainty.
2. Capture the unresolved commit set and missing anchor proof.
3. Route back through `$skill-hub` or `request-loopback-resume`.
