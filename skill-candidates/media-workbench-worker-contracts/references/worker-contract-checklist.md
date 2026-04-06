# Media Workbench Worker Contract Checklist

Use this reference when a change touches the Media Workbench worker contract.

## Contract Surfaces

- `/health`
- `/ready`
- `/v1/media-agent/status`
- `/v1/media-agent/jobs`
- `/v1/media-agent/summary`

## Required Alignment

Keep these surfaces aligned in one pass:

1. worker HTTP payloads
2. Electron IPC handlers
3. operator snapshot or runtime snapshot output
4. queue, cancel, retry, and resume-latest behavior
5. repo docs and tests

## Failure Patterns

- queue payload accepted by the worker but not reflected in desktop state
- resume target or latest failure no longer maps to a visible work item
- active job metadata disappears after refresh or restart
- desktop shell bootstraps a worker that does not satisfy the current status contract
- sister repos start depending on undocumented worker-only fields
