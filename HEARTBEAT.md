# HEARTBEAT.md

## Purpose

Recurring deterministic governance check for `skill-arbiter`.

## Standard heartbeat run

1. `python -m pytest -q tests/test_skill_audit.py tests/test_code_gap_sweep.py tests/test_workstream_resume.py`
1. `python -m pytest -q tests/test_comfy_media_pipeline_check.py`
1. Verify `AGENTS.md`, `BOUNDARIES.md`, and `INSTRUCTIONS.md` still match local-first guardrails.

## Result contract

- Return `HEARTBEAT_OK` only when checks pass.
- Report exact failing test module when a failure occurs.
