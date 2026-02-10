---
name: repo-b-local-bridge-orchestrator
description: Run credit-first local Agent Bridge orchestration in <PRIVATE_REPO_B> with strict read-only validation, bounded indexing, and fail-closed guidance hints. Excludes MCP Comfy diagnostics.
---

# REPO_B Local Bridge Orchestrator

Use this skill to run a manual local-first Agent Bridge workflow in `<PRIVATE_REPO_B>` and emit validated guidance hints without cloud fallback.

## Scope Boundary

- In scope: `/api/agent/*` readiness/tasks, bounded file indexing, `analyze_files` validation, and guidance hint output.
- Out of scope: `/api/mcp/*` operations and `shim.comfy.*` diagnostics.
- For MCP/Comfy operations, use `$repo-b-mcp-comfy-bridge`.

## Workflow

1. Confirm policy-safe environment (`read_only`, fail-closed).
2. Probe bridge readiness (`/health`, `/api/agent/capabilities`).
3. Build or refresh bounded metadata index on demand.
4. Query candidate files for the selected scope.
5. Submit read-only `analyze_files` task (`allow_write=false`, `dry_run=true`).
6. Validate bridge response with strict schema/evidence/confidence gates.
7. Emit normalized `guidance_hints` JSON and stop on failures.

## Drop-In Hook Files

Copy these files into `<PRIVATE_REPO_B>` before first run:

- `assets/repo_b/tools/local_bridge_orchestrator.py` -> `tools/local_bridge_orchestrator.py`
- `assets/repo_b/tools/local_bridge_validate.py` -> `tools/local_bridge_validate.py`
- `assets/repo_b/tools/local_bridge_orchestrator.example.env` -> `tools/local_bridge_orchestrator.example.env`
- `assets/repo_b/tests/tools/test_local_bridge_orchestrator.py` -> `tests/tools/test_local_bridge_orchestrator.py`
- `assets/repo_b/tests/tools/test_local_bridge_validate.py` -> `tests/tools/test_local_bridge_validate.py`

## Required Environment (PowerShell)

```powershell
$env:REPO_B_LOCAL_ORCH_ENABLED = "1"
$env:REPO_B_LOCAL_ORCH_CONFIDENCE_MIN = "0.85"
$env:REPO_B_LOCAL_ORCH_EVIDENCE_MIN = "2"
$env:REPO_B_LOCAL_ORCH_FAIL_CLOSED = "1"
$env:REPO_B_LOCAL_ORCH_MAX_HINTS = "12"
$env:REPO_B_CONTINUE_BRIDGE_ENABLED = "1"
$env:REPO_B_CONTINUE_MODE = "read_only"
$env:REPO_B_CONTINUE_ALLOWED_ROOTS = "$env:USERPROFILE\Documents\GitHub\<PRIVATE_REPO_B>"
```

## Run Command

Run from `<PRIVATE_REPO_B>` root:

```bash
python tools/local_bridge_orchestrator.py \
  --task ticket-123 \
  --prompt-file .codex/local_prompts/ticket-123.txt \
  --scope connector \
  --json-out .codex/local_bridge/ticket-123.json
```

## Usage Guardrails

Use your real usage history before scale-up:

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

## References

- `references/orchestrator-workflow.md`
- `references/validation-contract.md`
- `references/mx3-phase2-roadmap.md`
