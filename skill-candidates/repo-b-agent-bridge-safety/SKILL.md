---
name: repo-b-agent-bridge-safety
description: Operate and secure the Continue Agent Bridge in <PRIVATE_REPO_B>. Use when configuring bridge modes, validating /api/agent endpoints, enforcing controlled-write safety gates, or diagnosing bridge availability and permission failures.
---

# REPO_B Shim Agent Bridge Safety

Use this skill for Agent Bridge setup and safety enforcement.

## Workflow

1. Configure bridge environment variables for session mode.
2. Validate capabilities endpoint and a read-only task.
3. Keep `read_only` as default; enable `controlled_write` only when required.
4. Enforce `allow_write` and apply gating rules.

## Required Environment (PowerShell)

```powershell
$env:REPO_B_CONTINUE_BRIDGE_ENABLED = "1"
$env:REPO_B_CONTINUE_BRIDGE_URL = "http://127.0.0.1:11420"
$env:REPO_B_CONTINUE_MODE = "read_only"
$env:REPO_B_CONTINUE_ALLOWED_ROOTS = "$env:USERPROFILE\Documents\GitHub\<PRIVATE_REPO_B>"
```

Optional controlled-write limits:

```powershell
$env:REPO_B_CONTINUE_WRITE_ALLOWED_ROOTS = "$env:USERPROFILE\Documents\GitHub\<PRIVATE_REPO_B>\repo_b_repo_b_python_shim,$env:USERPROFILE\Documents\GitHub\<PRIVATE_REPO_B>\tests"
$env:REPO_B_CONTINUE_APPLY_ENABLED = "0"
```

## API Checks

```powershell
Invoke-RestMethod http://127.0.0.1:9000/api/agent/capabilities | ConvertTo-Json -Depth 8
```

```powershell
$body = @{
  task_type   = "analyze_files"
  prompt      = "Summarize required docs changes."
  paths       = @("README.md", "docs/PROJECT_SCOPE.md", "docs/SCOPE_TRACKER.md")
  allow_write = $false
  dry_run     = $true
} | ConvertTo-Json -Depth 8
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:9000/api/agent/tasks" -ContentType "application/json" -Body $body
```

## Reference

- `references/bridge-safety-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
