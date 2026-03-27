# Qwen Training Desktop Runtime Surfaces

Primary surfaces:

- `apps/qwen-training-desktop/electron/`
- `apps/qwen-training-desktop/README.md`
- `apps/local_dashboard/`
- `tools/qwen_training_workbench_agent.py`
- `tools/start_qwen_training_workbench_desktop.ps1`
- `tools/start_qwen_training_workbench_agent.ps1`

Primary HTTP endpoints:

- `GET /health`
- `GET /ready`
- `GET /v1/training-agent/status`
- `GET /v1/training-agent/jobs`
- `GET /v1/training-agent/campaigns`
- `GET /v1/training-agent/submissions`

Prefer the worker JSON over UI summaries when they disagree.
