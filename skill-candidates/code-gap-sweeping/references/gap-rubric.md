# Gap Rubric

Use this rubric to interpret findings emitted by `code_gap_sweep.py`.

## Severities

- `critical`: release-hygiene gaps on release-impacting changes.
- `high`: missing tests for changed code paths.
- `medium`: docs lockstep drift, or added `TODO`/`FIXME` markers.

## Category Definitions

1. `tests_missing`
   - Trigger: source-code changes detected without corresponding test-file changes.
   - Expected action: add/adjust focused tests in the same PR.

2. `docs_lockstep_missing`
   - Trigger: behavior-impacting file changes without updates to docs set.
   - Expected action: update README/scope/policy docs in lockstep or record explicit no-change review.

3. `todo_fixme_added`
   - Trigger: added patch lines include `TODO` or `FIXME`.
   - Expected action: resolve now or mark externally blocked with concrete requirement.

4. `release_hygiene_missing`
   - Trigger: release-impacting changes without both `pyproject.toml` and `CHANGELOG.md` modified in repos that already use this release contract.
   - Expected action: run release bump workflow and align changelog notes.

## Suggested Skill Lanes

- `tests_missing` -> `skill-common-sense-engineering`
- `docs_lockstep_missing` -> `docs-alignment-lock`
- `todo_fixme_added` -> `skill-common-sense-engineering`
- `release_hygiene_missing` -> `skill-arbiter-release-ops`
