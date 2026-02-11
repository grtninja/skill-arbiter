# Repo-Family Pipeline Matrix

Use `scripts/repo_family_pipeline.py` when the same gap-sweep and resume pipeline must be applied across repo families (`repo_a`, `repo_b`, `repo_c`, `repo_d`).

## What It Generates

1. Per-repo checkpoint pipeline commands:
   - `request-loopback-resume init`
   - per-repo `code_gap_sweep.py`
   - `request-loopback-resume set/validate/resume`
2. One all-repos gap sweep command.
3. Family skill-pack admission commands:
   - `scripts/arbitrate_skills.py` for each active family pack
   - `skill-installer-plus plan/admit` commands for each family skill
4. Optional bash script to execute the generated matrix.

## Command

```bash
python3 "${CODEX_HOME}/skills/code-gap-sweeping/scripts/repo_family_pipeline.py" \
  --repo "<PRIVATE_REPO_A>=/path/to/<PRIVATE_REPO_A>" \
  --repo "<PRIVATE_REPO_B>=/path/to/<PRIVATE_REPO_B>" \
  --family "<PRIVATE_REPO_A>=repo_a" \
  --family "<PRIVATE_REPO_B>=repo_b" \
  --since-days 14 \
  --json-out /tmp/repo-family-pipeline.json \
  --bash-out /tmp/repo-family-pipeline.sh
```

## Family Skill Packs

- `repo_a`: `repo-a-policy-selftest-gate`, `repo-a-coordinator-smoke`, `repo-a-telemetry-kv-guard`
- `repo_b`: `repo-b-local-bridge-orchestrator`, `repo-b-mcp-comfy-bridge`, `repo-b-comfy-amuse-capcut-pipeline`, `repo-b-thin-waist-routing`, `repo-b-preflight-doc-sync`, `repo-b-hardware-first`
- `repo_c`: `repo-c-boundary-governance`, `repo-c-policy-schema-gate`, `repo-c-ranking-contracts`, `repo-c-shim-contract-checks`, `repo-c-trace-ndjson-validate`, `repo-c-persona-registry-maintenance`
- `repo_d`: `repo-d-ui-guardrails`, `repo-d-setup-diagnostics`, `repo-d-local-packaging`

Unmapped repos default to `generic` (no family skill pack).

## Notes

- Use explicit `--family name=family` assignments for deterministic routing.
- Use generated JSON as evidence artifact for planning and handoff lanes.
- Generated bash commands are non-destructive by default and run only the named scripts.
