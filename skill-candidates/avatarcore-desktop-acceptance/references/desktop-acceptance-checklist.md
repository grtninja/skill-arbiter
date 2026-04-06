# AvatarCore Desktop Acceptance Checklist

Use this reference when AvatarCore is being treated as a workstation app.

## Minimum Gates

1. a repo-owned combined launcher exists
2. the visible frontend and required backend start together
3. no stale repo-owned app windows remain before relaunch
4. no empty shell windows remain after launch
5. `/health` reports operator-usable readiness

## Failure Patterns

- backend-only proxy launch reported as full app readiness
- visible frontend absent or started from an ad hoc path
- stale repo-owned windows left open across relaunches
- health output says `ok` but does not reflect the actual visible app state
- docs describe a workstation-ready app before the combined launcher exists
