# Routing Contract Checklist

Use this checklist when enforcing one-brain routing for VRM + PC Control + shim.

## 1. Authority Contract

- Public local model authority is `http://127.0.0.1:9000/v1`.
- Hosted 27B authority lane is `http://127.0.0.1:2337/v1`.
- `http://127.0.0.1:1234/v1` and the LM Studio loaded-models panel are operator surfaces only, not routing authority.
- PC Control remains governance/control plane (`http://127.0.0.1:8890`).
- VRM runtime lane remains avatar runtime (`http://127.0.0.1:5175`).
- Canonical repo roots stay under `G:\GitHub`; legacy `Documents\GitHub` paths are aliases only.

## 2. Research-First Gate

- PC Control local-agent or status-surface evidence collected first:
  - `/v1/agent-fabric/contracts/endpoints`
  - `/v1/agent-fabric/models/local`
  - `/v1/agent-fabric/local-agent/chat` (research-only)
- Sub-agent evidence collected from all three repos:
  - the shim repo
  - the PC Control repo
  - the avatar runtime repo
- If cloud sidecars are required, keep them lower-reasoning and low-cost.

## 3. No-Port-Drift Rule

- Do not replace `9000` as the public endpoint in defaults/profile files.
- Do not invent new public ports for operator-facing chat routes.
- Internal helper ports are allowed only when they remain private and documented.

## 4. Post-Change Validation

- `GET /v1/models?health=1` on `9000` returns expected model inventory.
- One routed chat call succeeds through the shim public lane.
- PC Control and VRM runtime health endpoints remain online.
- Any degraded lane is explicitly reported with status code and failure text.
