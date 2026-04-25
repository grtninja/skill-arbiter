---
name: "qwen-training-desktop-ops"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Operate the local Qwen Training Workbench desktop shell and its `9041` worker as one restart-safe local contract. Use when fixing or validating the Electron shell, launcher path, local dashboard load, queue or campaign controls, job visibility, or desktop startup acceptance for the private training app."
---

# Qwen Training Desktop Ops

Use this skill for the local Qwen Training Workbench desktop surface, not just the long-running training lane behind it.

## Workflow

1. Treat the desktop shell and the `9041` worker as one owned local contract.
2. Validate the backend first:
   - `http://127.0.0.1:9041/health`
   - `http://127.0.0.1:9041/ready`
   - `http://127.0.0.1:9041/v1/training-agent/status`
3. Launch only through the canonical repo-owned desktop entrypoint.
4. Confirm the shell loads the worker UI from `http://127.0.0.1:9041/` instead of drifting to a packaged or remote surface.
5. Prefer worker truth over renderer assumptions for queue, campaigns, jobs, and submissions.
6. Keep the operator flow explicit:
   - desktop start
   - worker readiness
   - campaign or job submission
   - active and queued job visibility
   - artifact and runtime inspection
7. Restart the desktop after Electron-shell changes. Do not claim UI fixes without a real relaunch.

## Canonical Commands

Desktop launch:

```powershell
powershell -ExecutionPolicy Bypass -File `
  <training-workbench-root>\tools\start_qwen_training_workbench_desktop.ps1
```

Worker lifecycle:

```powershell
powershell -ExecutionPolicy Bypass -File `
  <training-workbench-root>\tools\start_qwen_training_workbench_agent.ps1

powershell -ExecutionPolicy Bypass -File `
  <training-workbench-root>\tools\stop_qwen_training_workbench_agent.ps1

powershell -ExecutionPolicy Bypass -File `
  <training-workbench-root>\tools\get_qwen_training_workbench_agent_status.ps1
```

Health checks:

```bash
curl http://127.0.0.1:9041/health
curl http://127.0.0.1:9041/ready
curl http://127.0.0.1:9041/v1/training-agent/status
curl http://127.0.0.1:9041/v1/training-agent/jobs
curl http://127.0.0.1:9041/v1/training-agent/campaigns
```

## Runtime Truth

Prefer these surfaces as the source of truth:

- `apps/qwen-training-desktop/`
- `apps/local_dashboard/`
- `tools/qwen_training_workbench_agent.py`
- `evidence/agent_runtime/qwen_training_workbench_agent_state.json`
- `evidence/agent_runtime/jobs/`
- `evidence/agent_runtime/submissions/`

## Scope Boundary

Use this skill for the training desktop shell, launcher, worker coupling, and operator-facing runtime views.

Do not use this skill for:

1. dataset-factory or continuation-batch decision making without the desktop/operator context
2. generic Electron packaging work outside this app
3. docs-only wording cleanup

## References

- `references/ops-checklist.md`
- `references/runtime-surfaces.md`
