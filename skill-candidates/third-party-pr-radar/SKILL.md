---
name: third-party-pr-radar
description: Build a weekly third-party white-hat PR target board from local clone references, live GitHub state, and the current contribution ledger. Use when ranking the next public PR candidates, correlating them to existing lanes, producing cross-repo evidence blocks, or preparing the ledger/review loopback for future public submissions.
---

# Third-Party PR Radar

Use this skill to produce the weekly scouting board for third-party white-hat PR work.

This skill is the glue layer. It does not replace the execution chain for real PR work.

## Summary

Use this lane when the job is to:

- rank the next `10` public white-hat PR targets
- correlate candidates to the current third-party/public PR ledger
- attach success-chance and threat-level scoring
- prepare compact cross-repo evidence blocks for recurring bug classes
- capture repo-native validation lanes before a PR exists
- wire the chosen target back into the Codex review and contribution-ledger loop
- preserve the standing public-submission rule that clean merge into `main` is the target, not branch-only PR churn

## Required Chain

Route through this order:

`$skill-hub` -> `$request-loopback-resume` -> `$third-party-pr-radar`

When a target is chosen for real action, hand off to:

`$white-hat` -> `$github` -> `$skill-common-sense-engineering` -> `$skill-enforcer`

Optional follow-up skills:

- `$gh-address-comments` when an open PR already exists and review feedback needs action
- `$gh-fix-ci` when the target lane already has failing GitHub Actions
- `$safe-mass-index-core` when the clone scan needs bounded metadata-only discovery

## Authority Contract

Capture local truth before scouting:

1. Refresh the stale-process culprit map.
2. Treat `G:\GitHub` as the canonical repo root.
3. Treat `http://127.0.0.1:9000/v1` and `http://127.0.0.1:2337/v1` as authoritative model lanes.
4. Treat `http://127.0.0.1:1234/v1` only as a non-authoritative operator surface.
5. Prefer PC Control and harness status surfaces before assuming missing context.

## Sources Of Truth

Read these first:

- `<PRIVATE_REPO_ROOT>\reports\2026-04-12\third_party_weekly_white_hat_protocol.md`
- `<PRIVATE_REPO_ROOT>\reports\2026-04-12\third_party_target_board_2026-04-12.md`
- `<PRIVATE_REPO_ROOT>\reports\2026-04-12\third_party_skill_chain_2026-04-12.md`
- `%USERPROFILE%\.codex\workstreams\live_contribution_ledger.md`
- `%USERPROFILE%\.codex\workstreams\public_pr_status_live_latest.json`
- local clone roots:
  - `<PRIVATE_REPO_ROOT>`
  - `<PRIVATE_REPO_ROOT>`

Only read more when one of those surfaces is insufficient.

See:

- `references/protocol-source.md`
- `references/scoring-rubric.md`
- `references/review-loopback.md`

## Workflow

1. Capture local continuity and live ledger state.
2. Build the candidate pool from the local third-party clone roots and any already-ranked board artifacts.
3. Recheck live GitHub overlap:
   - open PRs in the candidate repo
   - exact-surface overlap if known
   - whether Eddie already has an active public lane in that repo
4. Build a repo-native validation map:
   - workflow lane names that would matter for the likely fix
   - changed-scope or docs-only routing if the repo exposes it
   - changed-extension or changed-package routing if the repo exposes it
   - the narrow local commands that match those lanes
   - whether the most recent visible red is `stale_red`, `active_red`, `pending`, or `clean`
5. Score each candidate with:
   - `value_fit`
   - `visibility`
   - `ease`
   - `acceptance_odds`
   - `overlap_penalty`
6. Derive two reporting fields:
   - `success_chance` as a percent estimate
   - `threat_level` as `low`, `medium`, `high`, or `critical`
7. Correlate the board directly to the live contribution ledger:
   - `ledger_overlap`: `none`, `same_repo`, `same_surface`, or `active_lane`
   - `sister_refs`: merged, adopted-upstream, or open related public lanes
   - `review_loop_ready`: whether the Codex connector plus queued review surfaces are reachable
8. Start a live ledger watch for the chosen lane before code changes begin:
   - record the candidate selection
   - record branch or worktree start
   - refresh the public PR board before push or PR open
   - upsert review-run ids, validation artifacts, push urls, and PR urls as they appear
9. Preserve clean-merge targeting:
   - treat clean merge into `main` as the default finish state
   - score down or skip lanes that are likely to create out-of-date, conflict-heavy, or branch-only noise
   - refresh overlap and base-branch movement before push so the lane still has a plausible clean-merge path
10. When the bug class is recurring, build one compact cross-repo evidence block.
11. Output the chat-ready ranked board plus artifact paths.
12. If the user wants to act on a target, hand off to the execution chain instead of implementing inside this skill.

## Output Contract

Produce:

1. A ranked top-10 list with:
   - repo
   - target issue, workflow, or file
   - success chance
   - threat level
   - validation map
   - one-sentence why
2. A ledger-correlation note for each top candidate:
   - whether an Eddie lane is already active in that repo
   - whether the repo is absent from the current public board
   - whether there is a sister-fix pattern from current wins
3. A current-head CI note for the highest-value active lanes:
   - `current_head_sha`
   - `ci_state`: `clean | stale_red | active_red | pending`
   - `narrow_validation`: the shortest repo-native rerun path
4. A compact cross-repo evidence block for the highest-value recurring bug families
5. A handoff note naming the next execution chain
6. A ledger-watch note naming:
   - the artifact or endpoint being watched
   - when it must be refreshed again
   - the next event that requires an upsert
7. A clean-merge note stating whether the lane still looks mergeable with a narrow patch, low overlap risk, and a plausible path to merge into `main`

Use:

- `templates/board_template.md`
- `templates/ecosystem_evidence_block.md`
- `templates/chat_report_template.md`

## Review Loopback

Before claiming a candidate is ready for action, check the Codex review loop:

1. `GET /v1/agent-fabric/connectors/codex/status`
2. `POST /v1/agent-fabric/plugins/local-codex-harness/session/prepare`
3. `POST /v1/agent-fabric/code-review-runs` for the chosen working diff
4. `POST /v1/agent-fabric/contributions` to persist artifacts and PR links

If that loop is degraded, say so explicitly and treat the lane as manual-preflight-only evidence rather than a clean local review pass.

Exact endpoint notes and minimal request shapes are in `references/review-loopback.md`.

## Live Ledger Rule

The contribution ledger is not a post-hoc report surface.

Once a lane moves from scouting to execution, keep the live ledger updated as work happens:

- candidate selected
- exact-surface overlap recheck completed
- worktree or branch created
- narrow validation passed or failed
- queued review run created or degraded
- push completed
- PR opened
- bot review or maintainer review arrived

If the board changes while the lane is active, refresh the public PR ledger before the next push or PR reply.

## Clean Merge Rule

Third-party/public contribution success is not "a branch exists" or "a PR was opened."

Keep the scouting and execution lanes aimed at a clean merge into `main`:

- prefer small, low-overlap patches that can merge without maintainers untangling adjacent churn
- avoid crowded or fast-moving exact surfaces unless the value clearly justifies the conflict risk
- refresh base freshness, open-PR overlap, and current-head state before push so a previously good lane has not drifted into merge noise
- if a lane no longer has a credible clean-merge path, downgrade it in the board or move it back to scout-first

## CI-Derived Validation Rule

Do not stop at "this repo has CI."

Build a validation map from the repo's actual workflow names, scripts, and change-routing helpers.

- Prefer repo-native routing helpers such as `docs_only`, changed-scope, changed-extension, or changed-package detection.
- Use the workflow names to choose the local proof, not vice versa.
- Keep a `stale_red` bucket separate from `active_red` so historical badge noise does not distort the board.
- OpenClaw is the model pattern:
  - change routing via `changed-scope` and `changed-extensions`
  - exact extension reruns via `scripts/test-extension.mjs`
  - narrow validation lanes such as `check`, `build-smoke`, `checks-fast-contracts-protocol`, and `gateway-watch-regression`
  - sharded extension failures that should not automatically expand into a whole-repo retest

If a repo does not expose this kind of structure, say so and fall back to the smallest obvious local proof.

## Cross-Repo Evidence Rule

Do not stop at "we fixed something similar elsewhere."

When the flaw class is genuinely recurring:

- use `2-4` public references max
- state the flaw class in one sentence
- state why this repo is another instance of that class in one sentence
- prefer merged or adopted-upstream public lanes first

Keep it factual, compact, and public-safe.

## Scope Boundary

Use this skill for scouting, ranking, correlation, and handoff only.

Do not use this skill to:

- implement the target fix
- reply to PR comments
- debug CI
- open or push a PR directly

Those actions belong to the follow-on chain.

## References

- `references/protocol-source.md`
- `references/scoring-rubric.md`
- `references/review-loopback.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. capture the stale-process artifact, live ledger snapshot, and any overlap uncertainty
2. route back through `$skill-hub`
3. resume only after the next step is one of:
   - rebuild the board
   - tighten the overlap check
   - hand off one chosen target into the execution chain
