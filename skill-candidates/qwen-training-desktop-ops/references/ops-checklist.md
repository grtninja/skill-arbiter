# Qwen Training Desktop Ops Checklist

1. Launch the desktop through the canonical PowerShell entrypoint.
2. Confirm `9041` answers `/health`, `/ready`, and `/v1/training-agent/status`.
3. Confirm the desktop loads the local worker surface from `http://127.0.0.1:9041/`.
4. Verify the operator can see campaigns, jobs, and submissions from worker-backed data.
5. If a desktop or worker bug is suspected, capture the worker JSON before trusting the renderer summary.
6. If Electron changes were made, relaunch the desktop before closing the lane.
