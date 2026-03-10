---
name: repo-a-host-admin-ops
description: Operate and validate <PRIVATE_REPO_A> admin-host desktop, client-host surfaces, and USB host-bundle workflows. Use when changing admin terminal UIs, host packaging/install scripts, startup acceptance, or USB-delivered host updates.
---

# Repo A Host Admin Ops

Use this skill for `<PRIVATE_REPO_A>` host/admin desktop and host-bundle work.

## Workflow

1. Read `AGENTS.md`, `README.md`, and the current host/install runbooks first.
2. Identify which lane changed:
   - admin desktop
   - client/host terminal
   - host bundle/config
   - USB install/update flow
3. For workstation admin-host work:
   - validate the visible admin app
   - reject backend-only success
   - respect any machine-specific rule about whether the admin desktop is the host lane
4. For USB host-bundle work:
   - run `$usb-export-reconcile` first
   - compare bundle drift before applying anything
5. Validate config and startup contracts after changes.
6. Report host/admin drift explicitly if startup or package expectations are still not aligned.

## Canonical Operations

Run from `<PRIVATE_REPO_A>` root when appropriate:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\open-admin-terminal.ps1
```

Host-bundle review lane:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\review_usb_host_bundle.ps1
```

Only use the separate host backend path on actual host-machine lanes where that path is intended.

## Scope Boundary

Use this skill only for `<PRIVATE_REPO_A>` host/admin desktop and USB host-bundle lanes.

Do not use it for:

1. Pure coordinator smoke tests.
2. General repo-A selftest gating without host/admin impact.
3. Repo-B or Repo-D startup lanes.

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture the changed host/admin surfaces and current startup evidence.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
