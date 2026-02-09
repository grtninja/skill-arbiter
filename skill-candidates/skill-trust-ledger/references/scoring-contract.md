# Scoring Contract

## Ledger Shape

- `version`
- `updated_at`
- `events[]`

`events[]` row:

- `timestamp`
- `skill`
- `event`
- `weight`
- `source`
- `note`

## Weight Model

- success: +3
- restored: +8
- warn: -4
- throttled: -7
- failure: -10
- disabled: -18
- quarantined: -20

## Score/Tier Mapping

- score starts at 50 per skill in the report window
- clamp final score to `[0, 100]`
- `>=80`: trusted
- `>=60`: observe
- `>=40`: restricted
- `<40`: blocked
