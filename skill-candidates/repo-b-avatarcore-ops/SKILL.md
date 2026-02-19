---
name: repo-b-avatarcore-ops
description: Run and validate <PRIVATE_REPO_B> AvatarCore proxy, provider routing, and Unreal bridge lifecycle surfaces.
---

# Repo B AvatarCore Operations

Use this skill for AvatarCore proxy and bridge-related changes in `<PRIVATE_REPO_B>`, including endpoint contract edits, provider configuration, and startup smoke checks.

## Workflow

1. Read `docs/AGENTS.md` and repository boundary docs.
2. Confirm local startup path works:
   - `python -m uvicorn avatarcore_proxy.main:app --host 127.0.0.1 --port 8000 --reload`
3. Run deterministic contract smoke tests:
   - `avatarcore_proxy/tests/test_integration_smoke.py`
   - `avatarcore_proxy/tests/test_proxy_smoke.py` (if present)
   - `avatarcore_proxy/tests/test_config_loader.py` (if provider/env override edits occurred)
4. Validate HTTP contract surface and bridge session lifecycle.
5. Capture evidence for any changed provider-routing or policy-flow behavior.

## Canonical Commands

From `<PRIVATE_REPO_B>` root:

```bash
python -m pytest avatarcore_proxy/tests/test_integration_smoke.py avatarcore_proxy/tests/test_proxy_smoke.py avatarcore_proxy/tests/test_config_loader.py
```

Contract smoke checks:

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/v1/avatarcore/query -H 'content-type: application/json' -d '{"character":"Penny","user_input":"Ping"}'
curl -s -X POST http://127.0.0.1:8000/v1/avatarcore/bridge/session -H 'content-type: application/json' -d '{"agent_mode":"smoke"}'
curl -s http://127.0.0.1:8000/v1/avatarcore/bridge/<session_id>/heartbeat -X POST -H 'content-type: application/json' -d '{"status":"ok"}'
curl -s -X DELETE http://127.0.0.1:8000/v1/avatarcore/bridge/<session_id>
```

Environment override diagnostic:

```bash
$env:AVATARCORE_CONFIG__PROVIDERS__LLM__ORDER__0="ollama"
python -m pytest avatarcore_proxy/tests/test_config_loader.py
```

## Guardrails

- Keep `/v1/avatarcore/bridge/*` and `/v1/avatarcore/*` payload contracts stable unless a migration is explicitly approved.
- Keep sanitized metadata and policy-gate behavior explicit and deterministic.
- Fail on contract shape drift in changed endpoints, including status codes and required keys.

## Scope Boundary

Use this skill only for the `repo-b-avatarcore-ops` lane and workflow defined in this file and its references.

Do not use this for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## Reference

- `references/avatarcore-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture the failing endpoint and test evidence.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
