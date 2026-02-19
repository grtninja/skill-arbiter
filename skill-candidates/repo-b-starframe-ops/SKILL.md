---
name: repo-b-starframe-ops
description: Validate <PRIVATE_REPO_B> STARFRAME API, AvatarCore proxy, persona registry, and degraded-mode guardrails.
---

# Repo B STARFRAME Ops

Use this skill for STARFRAME runtime contract and persona/runtime behavior changes in `<PRIVATE_REPO_B>`.

## Workflow

1. Read `AGENTS.md`, `BOUNDARIES.md`, and `INSTRUCTIONS.md` before edits.
2. Confirm test scope from touched files:
   - `starframe/` and `starframe/proxy` flows
   - `tests/proxy` intent routing and fail-closed behavior
   - `tests/starframe` persona/runtime policy and scoring surfaces
3. Run focused test and contract checks for any changed STARFRAME path.
4. Validate proxy + service endpoints in smoke mode for stable, contract-safe responses.
5. Verify scaling/telemetry changes preserve existing contract fields and degraded-mode transitions.

## Canonical Commands

Run from `<PRIVATE_REPO_B>` root:

```bash
python -m pytest tests/proxy/test_avatar_proxy_core.py tests/starframe/test_persona_registry.py
python -m pytest tests/starframe/test_provider_score.py tests/starframe/test_degraded_mode_rules.py
python -m pytest tests/starframe/test_unified_api.py tests/api/test_starframe_service.py
```

Optional strict lint/test lane:

```bash
ruff check starframe tests
pytest -q
```

## Runtime Smoke Checks

```bash
python -m starframe --host 127.0.0.1 --port 9010 --no-start-services
curl -s http://127.0.0.1:9010/health
curl -s http://127.0.0.1:9010/v1/unified/status
curl -s http://127.0.0.1:9010/v1/shim/rag/status
```

## Proxy Contract Guards

- Keep `starframe/proxy/avatar.py` dispatch/heartbeat behavior fail-closed when intent payloads are invalid.
- Preserve `AvatarProxyCore` budget and penalty math unless migration is documented.
- Preserve stable response keys under `Persona` and `telemetry` payloads when scaling/energy logic changes.

## Scope Boundary

Use this skill only for STARFRAME/AvatarCore proxy and persona-runtime governance in `<PRIVATE_REPO_B>`.

Do not use this for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## Reference

- `references/starframe-checklist.md`

## Loopback

If the lane is unresolved, blocked, or ambiguous:

1. Capture failing endpoint/tests and failed assertion details.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
