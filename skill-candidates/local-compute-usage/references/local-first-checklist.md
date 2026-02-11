# Local-First Checklist

Use this checklist before any local compute workflow that must avoid remote routing.

## 1) Workspace and Tooling

1. Confirm workspace is local and writable for the current task.
2. Confirm VS Code CLI is available (`code --version`).
3. Confirm required local CLIs/scripts are present in the repo.

## 2) Endpoint Locality

1. Enumerate required URLs (for example sidecar/shim, bridge, MCP, health routes).
2. Allow only local hosts by default:
   - `127.0.0.1`
   - `localhost`
   - `::1`
3. If additional hosts are required, explicitly document and approve them first.

## 3) MemryX Shim Priority

For `<PRIVATE_REPO_B>` lanes:

1. Verify Control Center health/readiness first.
2. Verify shim/hardware endpoints on loopback.
3. Run hardware diagnostics before changing runtime routing behavior.
4. Keep bridge and MCP diagnostics local-first.

## 4) Hardware Readiness Checks

1. Define at least one local hardware probe command for the active lane.
2. For MemryX flows, default to `acclBench --hello`.
3. Treat probe failures as fail-closed unless user explicitly approves a non-hardware path.
4. Capture the exact command and first failure line in evidence output.

## 5) Fail-Closed Conditions

Stop and reroute before mutations if any of the following are true:

1. Required URL host is non-local and unapproved.
2. VS Code/local CLI preflight fails for a required local workflow.
3. Endpoint probe fails in a workflow that requires live local service checks.
4. Hardware readiness probe fails in a hardware-backed workflow.

## 6) Evidence Capture

Capture and keep:

1. Preflight JSON output.
2. Endpoint list used for locality checks.
3. Hardware probe command(s) and result summary.
4. Any fail-closed reason and the reroute target skill.
