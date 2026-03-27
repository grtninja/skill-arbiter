# Cybertron Fabric Admission Workflow

Use this workflow to keep the Cybertron lane bounded and auditable.

## Admission sequence

1. Reconcile repo roots and confirm the canonical workspace root.
2. Check WinRM auth state before any host bootstrap attempt.
3. Verify the MeshGPT host-terminal lane before model-plane assumptions.
4. Validate the canonical model matrix and remove ad hoc aliases.
5. Confirm Starframe offload state and VRM display readiness.
6. Run `skill-auditor`, then `skill-arbiter-lockdown-admission`, then `skill-enforcer`.

## Required evidence

- repo parity report
- host readiness report
- model matrix report
- audit summary
- admission or trust-ledger output when the skill changes materially
