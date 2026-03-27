# Runtime Surfaces

## App and Worker

- `apps/media-workbench-desktop/ui/`
  - renderer workflow, preview, queue, output view
- `apps/media-workbench-desktop/electron/`
  - preload bridge, main-process startup, native file picking
- `tools/media_workbench_agent.py`
  - queue owner and worker contract on `9040`

## Runtime Evidence

- `evidence/agent_runtime/media_workbench_agent_state.json`
- `evidence/agent_runtime/jobs/`
- `evidence/agent_runtime/submissions/`

## Operator Output Root

- `<media-workbench-output-root>\work_items`

This root is the operator-facing handoff location for work items and exports. It should be preferred over buried repo-internal output paths during normal desktop use.
