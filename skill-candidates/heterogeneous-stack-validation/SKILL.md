---
name: heterogeneous-stack-validation
description: Validate a mixed local-plus-remote AI stack with privacy-safe evidence, endpoint health checks, inference smokes, and repo lockstep gates. Use when a request spans multiple local services, remote hosts, and heterogeneous inference lanes that must be tested end to end without launching restricted avatar endpoints.
---

# Heterogeneous Stack Validation

Use this skill when one workflow must reconcile:

- the active workstation stack
- remote host endpoints
- mixed inference lanes
- policy/docs alignment
- privacy/public-shape gates

## Workflow

1. Confirm the control authority and startup contract for the current host.
2. Probe local health lanes first:
   - `skill-arbiter`
   - the approved private workstation control repos listed in the active machine roster
   - the approved private inference and bridge repos listed in the active machine roster
3. Probe remote host runtime contracts and record exact failures.
4. Run real inference smokes on every lane that is meant to be live.
5. Reconcile docs and open-diff reports with the observed runtime truth.
6. Run privacy/public-shape gates before closing the pass.
7. Record the outcome back into Skill Arbiter collaboration and skill-game lanes.
8. If a remote host package is stale, repair the authoritative repo/config/install sources first and treat GitHub sync plus reinstall as the preferred fix path.

## Required Evidence

- local health checks with exact status codes
- remote host health checks with exact status codes
- at least one successful real inference request for each live lane
- explicit contract-failure notes for any broken lane
- repo test/build output for each touched repo
- privacy/public-shape gate results for public repos

## Guardrails

- Do not launch local avatar endpoints when the task forbids it.
- Treat already-running remote avatar surfaces as read-only probe targets only.
- Keep host-specific secrets, usernames, and absolute paths out of repo-tracked docs.
- Prefer loopback and LAN-local validation over cloud checks.
- Fail closed on missing health or inference contracts; do not call a lane healthy because a parent app window exists.

## Canonical Lanes

- Local workstation services:
  - `127.0.0.1:17665`
  - `127.0.0.1:9000`
  - `127.0.0.1:11420`
  - `127.0.0.1:8800`
  - `127.0.0.1:18789`
  - `127.0.0.1:8890`
  - `127.0.0.1:8895`
- Remote hosts:
  - `<remote-host-a>`
  - `<remote-host-b>`

## Output

Produce:

- a concise runtime truth table
- repo validation results
- remaining blockers
- follow-up skill work worth creating, upgrading, or consolidating

## References

- `references/validation-contract.md`

## Loopback

If the stack cannot be validated cleanly:

1. capture the failing endpoint or repo gate with exact evidence
2. repair the smallest authoritative layer first
3. rerun only the affected validation slice
4. record the repaired result in Skill Arbiter collaboration state
