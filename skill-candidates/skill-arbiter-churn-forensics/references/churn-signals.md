# Churn Signals

Primary indicators:
- `samples`: per-second rg process counts.
- `max_rg`: highest rg count observed.
- `persistent_nonzero`: threshold streak indicator.
- `action`: `kept` or `deleted` arbitration outcome.
- `note`: reason for action (blacklist, immutable override, third-party deny, promotion).
