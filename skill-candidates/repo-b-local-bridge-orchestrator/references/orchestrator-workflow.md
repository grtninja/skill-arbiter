# Local Bridge Orchestrator Workflow

Use this runbook after copying drop-in files into `<PRIVATE_REPO_B>`.

## 1) Preflight

1. Confirm bridge mode is read-only:
   - `REPO_B_CONTINUE_MODE=read_only`
2. Confirm fail-closed mode:
   - `REPO_B_LOCAL_ORCH_FAIL_CLOSED=1`
3. Confirm allowed roots are narrow and local.

## 2) Runtime Readiness

Run quick endpoint checks from `<PRIVATE_REPO_B>`:

```bash
curl http://127.0.0.1:9000/health
curl http://127.0.0.1:9000/api/agent/capabilities
```

If either check fails, stop and diagnose bridge availability before continuing.

## 3) Execute Manual Task

```bash
python tools/local_bridge_orchestrator.py \
  --task ticket-123 \
  --prompt-file .codex/local_prompts/ticket-123.txt \
  --scope connector \
  --json-out .codex/local_bridge/ticket-123.json
```

Scope options:

- `connector`
- `service`
- `route`
- `config`

## 4) Exit Codes

- `0`: success with validated `guidance_hints`
- `10`: bridge unavailable
- `11`: index unavailable
- `12`: validation failed
- `13`: policy violation

## 5) Output Contract

The JSON artifact includes:

- `status`
- `task_id`
- `bridge_probe`
- `index_run`
- `validation`
- `guidance_hints`
- `timing_ms`
- `reason_codes`

## 6) Retry Behavior

Index retries are bounded:

1. First build: `--max-seconds 25`
2. Retry only when candidate list is empty and the build stopped by budget.
3. Retry build once with `--max-seconds 40`.
4. Stop deterministically after retry.

## 7) Cost Tracking

Before rollout and weekly thereafter:

```bash
python3 "$CODEX_HOME/skills/usage-watcher/scripts/usage_guard.py" analyze \
  --input /path/to/usage.csv \
  --window-days 30 \
  --format table
```

```bash
python3 "$CODEX_HOME/skills/usage-watcher/scripts/usage_guard.py" plan \
  --monthly-budget <credits> \
  --reserve-percent 20 \
  --work-days-per-week 5 \
  --sessions-per-day 3 \
  --burst-multiplier 1.5 \
  --format table
```
