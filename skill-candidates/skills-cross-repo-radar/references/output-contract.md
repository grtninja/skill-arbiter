# Output Contract

`repo_change_radar.py` emits a JSON payload with:

- `pass`: overall boolean
- `generated_at`: UTC ISO timestamp
- `window_days`: lookback window used
- `blockers[]`: parse/runtime blockers
- `summary`: aggregate counters
- `repos[]`: per-repository rows

Per-repo row fields include:

- `repo`, `path`, `ok`
- `last_commit` (`hash`, `timestamp`, `subject`)
- `commit_count`, `commits_sample[]`
- `changed_files_count`, `changed_files_sample[]`
- `dirty_files_count`, `dirty_files_sample[]`
- `policy_change_count`, `contract_change_count`, `skill_change_count`
- `policy_paths[]`, `contract_paths[]`, `skill_paths[]`
- `risk_flags[]` (`policy_sensitive`, `contract_surface`, `skill_system`, `dirty_worktree`)

Use this report as an evidence input for:

- skills discovery/curation
- skills consolidation planning
- cross-repo policy gate reviews
