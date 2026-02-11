# Skill Installer Plus Learning Loop

Use this loop to make installs safer and faster over time.

## Inputs

- Candidate skills under `skill-candidates/` (or another local source root).
- Existing local control files under `$CODEX_HOME/skills`:
  - `.blacklist.local`
  - `.whitelist.local`
- Optional trust report from `skill-trust-ledger`.

## Cycle

1. Run `plan` to score candidates.
2. Install only the top candidates that are not blocked.
3. Run `admit` so `skill-arbiter` captures churn evidence.
4. Store arbiter outcomes in the installer ledger.
5. Record manual `feedback` events after real usage.
6. Repeat from step 1.

## Scoring Heuristics

Recommendation score combines:

1. Arbiter history (`kept`, `deleted`, `persistent_nonzero`, `max_rg` trend).
2. Manual feedback weights (`success`, `warn`, `failure`, `disabled`, `restored`).
3. Trust-tier bonus when a trust report is supplied.
4. Local blacklist/whitelist state from destination control files.

The score drives a recommendation state:

- `install`: strong candidate.
- `review`: acceptable but needs human check.
- `defer`: low confidence; wait for more evidence.
- `blocked`: do not install until evidence improves.

## Operating Notes

- Keep installs local-first (`--source-dir`) and use `--personal-lockdown`.
- Prefer explicit `--arbiter-json` and `--json-out` paths for reproducible evidence.
- Use `admit --dry-run` for policy rehearsal before any mutation.
