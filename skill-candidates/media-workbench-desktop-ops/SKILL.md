---
name: media-workbench-desktop-ops
description: Operate the STARFRAME Media Workbench desktop app and its local 9040 worker as one restart-safe local contract. Use when fixing or validating the Electron shell, source staging flow, prompt-head automation, queue submission, live telemetry, output preview, or desktop startup acceptance for the private media app.
---

# Media Workbench Desktop Ops

Use this skill for the local STARFRAME Media Workbench app surface, not just the raw render lanes behind it.

## Workflow

1. Confirm the machine is in `media_workbench` mode before touching the app.
2. Treat the Electron shell and the `9040` worker as one owned contract.
3. Validate the backend first:
   - `http://127.0.0.1:9040/health`
   - `http://127.0.0.1:9040/ready`
   - `http://127.0.0.1:9040/v1/media-agent/status`
4. Validate the trained prompt-head lane when source-analysis automation depends on it.
5. Prefer source-by-reference workflows. The app must bind the exact local file path without duplicating the source library.
6. Prefer automation-first UX:
   - source drop or pick should stage the file immediately
   - prompt generation should start automatically
   - the queue draft should become runnable without manual argument surgery
7. Keep the operator-facing workflow explicit:
   - source intake
   - prompt head / source analysis
   - automatic workflow launch
   - live telemetry and output review
8. Use the configured operator output root as the canonical handoff:
   - `<media-workbench-output-root>\work_items`
9. Restart the frontend after UI or Electron-shell changes. Do not claim UI fixes without a real desktop relaunch.

## Canonical Commands

Backend lifecycle:

```powershell
powershell -ExecutionPolicy Bypass -File `
  <media-workbench-root>\tools\start_media_workbench_agent.ps1

powershell -ExecutionPolicy Bypass -File `
  <media-workbench-root>\tools\stop_media_workbench_agent.ps1

powershell -ExecutionPolicy Bypass -File `
  <media-workbench-root>\tools\get_media_workbench_agent_status.ps1
```

Desktop lifecycle:

```powershell
powershell -ExecutionPolicy Bypass -File `
  <media-workbench-root>\tools\start_media_workbench_desktop.ps1
```

Health checks:

```bash
curl http://127.0.0.1:9040/health
curl http://127.0.0.1:9040/ready
curl http://127.0.0.1:9040/v1/media-agent/status
curl <prompt-head-lane>/health
curl <prompt-head-lane>/v1/models
```

## Runtime Truth

Prefer these surfaces as the source of truth:

- `apps/media-workbench-desktop/ui/`
- `apps/media-workbench-desktop/electron/`
- `tools/media_workbench_agent.py`
- `evidence/agent_runtime/media_workbench_agent_state.json`
- `evidence/agent_runtime/jobs/`
- `evidence/agent_runtime/submissions/`
- `<media-workbench-output-root>\work_items`

## Pass Criteria

At minimum, require:

1. the desktop shell starts through the canonical launcher
2. `9040` is healthy and ready
3. a dropped or picked source binds a real local path
4. source analysis can populate a workflow draft automatically
5. the active output view can preview the latest export without leaving the app
6. the app distinguishes active, queued, and completed work clearly for an operator

## Scope Boundary

Use this skill for the Media Workbench app shell, worker contract, and operator flow.

Do not use this skill for:

1. running the full Qwen teacher-student training lane
2. generic ComfyUI-only graph work without the desktop app
3. VRM avatar workflows

## References

- `references/ops-checklist.md`
- `references/runtime-surfaces.md`
