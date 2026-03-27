---
name: cybertron-fabric-host-ops
description: Audit Cybertron remote-host readiness, repo parity, WinRM auth-state, MeshGPT host-terminal bootstrap, canonical model-matrix validation, Starframe/Cybertron offload checks, and VRM display readiness.
---

# Cybertron Fabric Host Ops

Use this skill for Cybertron host governance when remote management, repo parity, model placement, or VRM display readiness need to be validated as one bounded lane.

## Workflow

1. Route the request through `skill-hub` and `skills-cross-repo-radar` first so the Cybertron lane is isolated from unrelated repo work.
2. Reconcile roots and parity before changing anything else:
   - compare `<external-candidate-root>` against any paired `$env:USERPROFILE\...` clone
   - confirm branch, HEAD, dirty state, and untracked state
3. Check Cybertron host readiness in order:
   - WinRM auth state
   - MeshGPT host-terminal bootstrap readiness
   - canonical model-matrix presence
   - Starframe mode/offload contract state
   - VRM display readiness
4. Use `multitask-orchestrator` only when the parity, model, and host-readiness lanes can run independently.
5. Validate the resulting package with `skill-auditor`, then pass admission through `skill-arbiter-lockdown-admission` and `skill-enforcer`.
6. Preserve trust evidence with `skill-trust-ledger` if the skill is materially updated again.

## Canonical Commands

Run from `<external-candidate-root>\skill-arbiter`:

```bash
python skill-candidates/cybertron-fabric-host-ops/scripts/cybertron_repo_parity.py --left <external-candidate-root>\skill-arbiter --right $env:USERPROFILE\...\skill-arbiter --json-out .tmp/cybertron-repo-parity.json

python skill-candidates/cybertron-fabric-host-ops/scripts/cybertron_model_matrix_check.py --json-out .tmp/cybertron-model-matrix.json

python skill-candidates/cybertron-fabric-host-ops/scripts/cybertron_host_readiness.py --host CYBERTRON_CORE --ports 5985 3389 1234 8892 --json-out .tmp/cybertron-host-readiness.json

python skill-candidates/cybertron-fabric-host-ops/scripts/cybertron_fabric_host_audit.py --skill-root skill-candidates/cybertron-fabric-host-ops --json-out .tmp/cybertron-fabric-host-audit.json
```

## Guardrails

- Do not invent fallback accounts, silent username fan-out, or arbitrary model aliases.
- Do not treat RDP as the primary automation lane.
- Do not expose unrestricted shell execution through this skill.
- Keep the canonical model family list aligned to the repo docs and generated catalog.
- Keep this skill scoped to Cybertron host readiness, parity, model, offload, and display checks.

## Scope Boundary

Use this skill only for Cybertron fabric host operations and the admission evidence needed to support them.

Do not use it for general desktop bring-up or unrelated repo work; route those through `$skill-hub` and the most specific matching skill.

## References

- `references/host-readiness.md`
- `references/repo-parity.md`
- `references/model-matrix.md`
- `references/admission-workflow.md`

## Loopback

If the lane is unresolved, blocked, or ambiguous:

1. Capture the failing check, affected host, and the exact missing readiness signal.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
