# Validation Contract

Use this skill when the validation target includes more than one of:

- multiple repositories
- multiple active desktop apps
- multiple inference backends
- multiple hosts

## Minimum pass condition

1. Every expected local service returns a health payload or an explicit contract failure.
2. Every live inference lane returns either a successful real response or an explicit runtime error.
3. Public-shape repositories pass privacy checks.
4. Touched repositories pass their targeted tests/builds or are explicitly blocked with evidence.
5. The final report distinguishes:
   - healthy
   - degraded
   - contract failure
   - intentionally excluded

## Canonical exclusions

- Do not start forbidden local avatar endpoints just to get a green report.
- Do not treat auth-gated endpoints as broken if the contract is auth-gated and the gate itself behaves correctly.
- Do not overwrite a running operator app if read-only probing is sufficient.

## Remote host repair rule

When a stale remote host is detected:

1. fix the authoritative repo-owned config or installer first
2. document the exact contract drift
3. prefer pull or sync plus reinstall on the target host
4. avoid treating one-off live host edits as the lasting fix
