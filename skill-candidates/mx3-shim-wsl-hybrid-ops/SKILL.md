---
name: mx3-shim-wsl-hybrid-ops
description: Operate and diagnose the Windows-host plus WSL-auxiliary split for memryx-mx3-python-shim. Use when validating hybrid service reachability, enforcing hardware-on-Windows boundaries, or debugging cross-host connectivity for ComfyUI and LM Studio helpers.
---

# MX3 Shim WSL Hybrid Ops

Use this skill for hybrid Windows+WSL operations.

## Workflow

1. Start Windows host services first.
2. Verify shim/pose/MCP listeners on Windows.
3. Verify WSL auxiliary endpoints are reachable from Windows.
4. Keep strict hardware checks in Windows lane only.

## Commands

Start host services:

```powershell
python tools/restart_local_apps.py
netstat -ano | findstr ":9000 :8787 :9550"
```

Check auxiliary endpoints:

```powershell
curl http://127.0.0.1:8188/system_stats
curl http://127.0.0.1:1234/v1/models
python tools/hybrid_doctor.py --pretty
```

Hardware strict (Windows-only):

```powershell
$env:MEMRYX_ONLY = "1"
$env:MEMRYX_FORCE_REAL = "1"
```

## Reference

- `references/hybrid-boundaries.md`
