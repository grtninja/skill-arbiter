# Ops Checklist

## Preflight

1. Confirm the machine is in `media_workbench` mode.
2. Confirm `9040` is reachable and `9041` is down.
3. Confirm the trained prompt-head lane is reachable when prompt generation depends on it.
4. Confirm the Pictures output root exists:
   - `<media-workbench-output-root>\work_items`

## Healthy Signs

- the Electron shell is visibly open through the canonical launcher
- `/health` and `/ready` both pass on `9040`
- the staged source shows both a preview and a real local path
- source analysis writes generated prompt text without manual intervention
- queue drafts contain a source path and a job name before launch
- the latest export can be previewed in-panel when present

## Failure Signs

- preview works but the bound source path is empty
- queue submissions launch without a positional source arg
- recent runs are dominated by failed jobs during normal operator use
- the app requires manual button choreography to do the obvious next step
- frontend changes were made but the desktop shell was not actually restarted
