---
name: repo-d-local-packaging
description: Run Windows-local packaging and release validation for <PRIVATE_REPO_D>. Use when building distributables, fixing packaging regressions, or validating installer/portable outputs without introducing CI workflows.
---

# Repo D Sandbox Local Packaging

Use this skill for deterministic local packaging in <PRIVATE_REPO_D>.

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

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
