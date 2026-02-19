---
name: repo-c-shim-contract-checks
description: Enforce REPO_B shim runtime contract expectations in <PRIVATE_REPO_C>. Use when changing shim-facing adapters, telemetry dependencies, integration tests, or fail-closed behavior tied to REPO_B_SIDECAR_URL and mock-shim fixtures.
---

# Repo C Shim Contract Checks

Use this skill for shim endpoint contract safety.

## Contract Requirements

- Runtime features requiring telemetry must fail closed when shim is unavailable.
- `REPO_B_SIDECAR_URL` config path remains explicit.
- CI-facing integration tests use mock shim fixtures, not real hardware.
- Do not mask core import failures with `pytest.importorskip()`.
- Audio and RAG routes tied to shim-backed services must keep closed-fallback behavior when sidecar signals are missing.
- Maintain stable payload contracts for `GET /health`, `/telemetry`, `/audio`, and `/rag` endpoints when fail-closed gates engage.

## Validation Commands

Run from `<PRIVATE_REPO_C>` root:

```bash
ruff check .
pytest -q
```

For focused shim contract review:

```bash
python - <<'PY'
from pathlib import Path
import re
patterns = [
    'REPO_B_SIDECAR_URL',
    'importorskip',
    'requires_real_sidecar',
    '/health',
    '/telemetry',
    '/audio',
    '/rag',
]
roots = ['AGENTS.md', 'tests', 'src', 'repo-c', 'repo_c_trace', 'ranking_engine']
for root in roots:
    p = Path(root)
    if not p.exists():
        continue
    for file in p.rglob('*'):
        if not file.is_file():
            continue
        if file.suffix.lower() not in {'.py', '.md', '.yml', '.yaml', '.json'}:
            continue
        text = file.read_text(encoding='utf-8', errors='ignore')
        for pattern in patterns:
            if re.search(pattern, text):
                break
        else:
            continue
        print(file)
PY
curl -s http://127.0.0.1:9000/health
curl -s http://127.0.0.1:9000/telemetry
curl -s http://127.0.0.1:9000/api/rag/status
```

## Scope Boundary

Use this skill only for the `repo-c-shim-contract-checks` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## Reference

- `references/shim-contract.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture the failing endpoint and test evidence.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
