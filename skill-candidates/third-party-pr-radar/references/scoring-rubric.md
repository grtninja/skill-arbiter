# Scoring Rubric

Base scoring:

- `value_fit` (`0-5`): how closely the lane matches the current win pattern
- `visibility` (`0-5`): repo prominence or adoption
- `ease` (`0-5`): how narrowly the likely fix can stay scoped
- `acceptance_odds` (`0-5`): how maintainer-safe and non-ideological the lane looks
- `overlap_penalty` (`0` to `-5`): repo churn, same-surface PR overlap, or policy drag

Derived reporting:

- `success_chance`
  - `80%+`: tiny scope, low overlap, issue-backed, maintainer-safe
  - `65-79%`: strong lane with some repo churn or acceptance drag
  - `45-64%`: good value but meaningful overlap or policy risk
  - `<45%`: high-value but noisy, crowded, or likely to be deprioritized
- `threat_level`
  - `low`: narrow hygiene or convenience defect
  - `medium`: reliability or correctness bug with contained blast radius
  - `high`: trust-boundary, parser, workflow, or runtime flaw with real operator risk
  - `critical`: high-visibility supply-chain or privileged workflow flaw on a sensitive surface

Validation-map discipline:

- High `success_chance` requires a narrow, credible local validation path.
- Reduce `success_chance` if the repo has only a broad or ambiguous test surface.
- Treat `stale_red` as signal for process noise, not automatic risk inflation.
- Raise `threat_level` when the repo's own CI isolates the issue to sensitive lanes such as workflows, auth, protocol/contracts, or extension boundary guards.

Ledger correlation tags:

- `none`
- `same_repo`
- `same_surface`
- `active_lane`

Do not inflate `success_chance` just because a repo is famous. Fame raises visibility, not always acceptance odds.
