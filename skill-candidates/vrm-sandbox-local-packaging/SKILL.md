---
name: vrm-sandbox-local-packaging
description: Run Windows-local packaging and release validation for VRM-Sandbox. Use when building distributables, fixing packaging regressions, or validating installer/portable outputs without introducing CI workflows.
---

# VRM Sandbox Local Packaging

Use this skill for deterministic local packaging in VRM-Sandbox.

## Workflow

1. Confirm Node LTS and npm workspace setup.
2. Run baseline checks before packaging:

```bash
npm install
npm run build
npm run lint
```

3. Build distributables:

```bash
npm run dist
```

4. Run packaging verification (desktop workspace):

```bash
npm --workspace apps/desktop run verify
```

5. Use PowerShell wrappers when requested:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
powershell -ExecutionPolicy Bypass -File scripts/package.ps1
```

## Evidence to Capture

- Commands executed and pass/fail status.
- Artifact paths under `apps/desktop/release`.
- Any blocker with explicit reproduction steps.

## References

- Packaging checklist: `references/packaging-checklist.md`
