---
name: skill-arbiter
description: Run the local NullClaw host security app for skill governance, curated-source discovery, guarded threat suppression, and self-governance on Windows hosts.
---

# Skill Arbiter

Use this skill when the work requires:

- live skill inventory and source reconciliation
- OpenClaw / NullClaw source-risk review
- VS Code/Codex built-in baseline drift checks
- Codex app / VS Code / GitHub Copilot instruction-surface interop checks
- local Codex config and loopback LM Studio advisor checks
- stale or untracked Python detection
- quarantine/admission decisions
- public-shape privacy validation
- self-governance of this repo and its release artifacts
- ownership/legitimacy vetting for installed, candidate, and official baseline skills

## Run

Install desktop launcher dependencies when using the managed security-console startup flow:

```bash
cd apps/nullclaw-desktop
npm install
```

Open the desktop app:

```bash
python scripts/nullclaw_desktop.py
```

Run the local loopback agent without the desktop shell:

```bash
python scripts/nullclaw_agent.py
```

Refresh the machine-generated catalog:

```bash
python scripts/generate_skill_catalog.py
```

Run the public-shape gate:

```bash
python scripts/check_private_data_policy.py
```

Run the public-release gate:

```bash
python scripts/check_public_release.py
```

## Behavior

1. Open the desktop shell first.
2. Attach or start the loopback agent.
3. Run privacy and self-governance checks.
4. Refresh the full skill/source inventory.
5. Surface the layered operator flow: startup, critical queue, active finding, mitigation, then evidence layers.
6. Keep destructive actions operator-confirmed.
7. Keep audit events in local state, not repo-tracked files.
8. Use a loopback LM Studio coding model for short coding-security guidance, preferring local Qwen when available.
9. Surface public support and security links as copy-only actions, not browser launches.
10. Keep subagent routing local-first: use healthy local OpenClaw-compatible lanes before cloud sidecars, and keep cloud sidecars on lower-reasoning bounded work unless the operator explicitly chooses otherwise.

## Local advisor

Default local advisor configuration:

```bash
$env:NULLCLAW_AGENT_BASE_URL="http://127.0.0.1:9000/v1"
$env:NULLCLAW_AGENT_MODEL="radeon-qwen3.5-4b"
$env:NULLCLAW_AGENT_ENABLE_LLM="1"
```

The advisor must remain local-only by default. The shared app-agent lane is `radeon-qwen3.5-4b`; Hui Hui stays reserved for avatar-specialized endpoints.

Subagent policy:

- The user chooses the operating mode; arbiter recommendations do not override operator intent.
- Healthy local subagents should be used first for quick bounded tasks.
- Cloud subagents should default to cheaper, lower-reasoning sidecar work.
- Fast mode is not part of the governed default path.

## Guardrails

- Do not launch an external browser as part of the normal app flow.
- Do not auto-install from unvetted third-party sources.
- Do not publish raw host evidence into repo-tracked files.
- Do not disable built-in VS Code/Codex skills to make overlays work.

## Related references

- `BOUNDARIES.md`
- `SECURITY.md`
- `references/skill-catalog.md`
- `references/skill-vetting-report.md`
- `references/vscode-skill-handling.md`
- `references/usage-chaining-multitasking.md`
- `references/OPENCLAW_NULLCLAW_THREAT_MATRIX_2026-03-11.md`
