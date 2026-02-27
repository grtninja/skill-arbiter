# Recommended Skill Portfolio (Current Set)

This portfolio uses only skills that exist in the current environment and repository overlay.

Policy:

- Keep VS Code/Codex built-ins enabled.
- Add repository skills from `skill-candidates/` as an overlay.
- Use `skill-arbiter` to moderate overlay safety; do not conflict with built-ins.

## Always-On Built-Ins

Keep these built-ins available for general utility:

1. `openai-docs`
2. `playwright`
3. `screenshot`
4. `gh-fix-ci`
5. `gh-address-comments`
6. `security-best-practices`
7. `security-threat-model`
8. `security-ownership-map`

High-value media stack:

1. `sora`
2. `imagegen`
3. `speech`
4. `transcribe`

## Overlay Core (Cross-Repo)

Install and maintain these overlay skills for most workstreams:

1. `skill-hub`
2. `skill-common-sense-engineering`
3. `usage-watcher`
4. `skill-cost-credit-governor`
5. `skill-cold-start-warm-path-optimizer`
6. `skill-installer-plus`
7. `skill-auditor`
8. `skill-enforcer`
9. `code-gap-sweeping`
10. `request-loopback-resume`
11. `playwright-edge-preference`

## Overlay Governance and Reliability

Use these when changing or admitting skills:

1. `skill-arbiter-lockdown-admission`
2. `skill-arbiter-churn-forensics`
3. `skill-arbiter-release-ops`
4. `skill-dependency-fan-out-inspector`
5. `skill-blast-radius-simulator`
6. `skill-trust-ledger`
7. `skills-consolidation-architect`
8. `skills-discovery-curation`
9. `docs-alignment-lock`

## Repo-Focused Overlay Sets

### `<PRIVATE_REPO_A>`

1. `repo-a-coordinator-smoke`
2. `repo-a-policy-selftest-gate`
3. `repo-a-telemetry-kv-guard`

### `<PRIVATE_REPO_B>`

Core:

1. `repo-b-control-center-ops`
2. `repo-b-hardware-first`
3. `repo-b-preflight-doc-sync`
4. `repo-b-agent-bridge-safety`
5. `repo-b-mcp-comfy-bridge`

Advanced:

1. `repo-b-avatarcore-ops`
2. `repo-b-starframe-ops`
3. `repo-b-thin-waist-routing`
4. `repo-b-wsl-hybrid-ops`
5. `repo-b-comfy-amuse-capcut-pipeline`
6. `repo-b-local-bridge-orchestrator`
7. `repo-b-local-comfy-orchestrator` (legacy wrapper)
8. `repo-b-mass-index-ops`

### `<PRIVATE_REPO_C>`

1. `repo-c-boundary-governance`
2. `repo-c-policy-schema-gate`
3. `repo-c-ranking-contracts`
4. `repo-c-trace-ndjson-validate`
5. `repo-c-persona-registry-maintenance`
6. `repo-c-shim-contract-checks`
7. `repo-c-mass-index-ops`

### `<PRIVATE_REPO_D>`

1. `repo-d-ui-guardrails`
2. `repo-d-setup-diagnostics`
3. `repo-d-local-packaging`
4. `repo-d-mass-index-ops`

## Large-Repo Discovery Set

1. `safe-mass-index-core`
2. `repo-b-mass-index-ops`
3. `repo-c-mass-index-ops`
4. `repo-d-mass-index-ops`

## Default Chain and Multitasking

Start with:

1. `skill-hub`
2. `skill-common-sense-engineering`
3. `usage-watcher`
4. `skill-cost-credit-governor`
5. `skill-cold-start-warm-path-optimizer`

Then add:

1. `code-gap-sweeping` for multi-repo diffs
2. `request-loopback-resume` for interruption-safe continuation
3. `skill-auditor` + `skill-enforcer` for governance closure

If `multitask-orchestrator` is available, use it for independent lanes. Otherwise, split and merge lanes manually with deterministic evidence.

Edge-first browser pattern:

1. `skill-hub`
2. `playwright-edge-preference`
3. `playwright-safe` (for low-churn execution)
4. `playwright` built-in for general browser flow extensions

## Admission Template

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  skill-hub skill-common-sense-engineering usage-watcher \
  skill-cost-credit-governor skill-cold-start-warm-path-optimizer \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown \
  --json-out /tmp/portfolio-admission.json
```

Target outcomes:

- `action=kept`
- `persistent_nonzero=false`
- `max_rg=0` preferred
