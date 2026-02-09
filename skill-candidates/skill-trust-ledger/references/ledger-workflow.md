# Ledger Workflow

## Event Sources

- manual operator review
- arbitration outcomes
- incident retrospectives

## Event Types

- `success`
- `warn`
- `throttled`
- `failure`
- `disabled`
- `quarantined`
- `restored`

## Routine

1. append events after significant outcomes
2. ingest arbiter output after each admission pass
3. generate weekly or biweekly reports
4. enforce policy by tier

## Recommended Policy by Tier

- `trusted`: normal invocation
- `observe`: normal invocation with post-run checks
- `restricted`: manual approval only
- `blocked`: deny by default
