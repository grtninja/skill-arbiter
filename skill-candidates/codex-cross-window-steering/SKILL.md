---
name: codex-cross-window-steering
description: Steer, brief, redirect, or rescue another live Codex agent in <PUBLIC_OPERATOR_SCOPE> using evidence-backed operator packets, clipboard handoff, and fail-closed workflow boundaries. Use when the operator asks to steer another Codex lane, coordinate multiple Codex windows, recover a degraded Codex thread, or pass instructions to a separate agent without changing model/config/runtime contracts.
---

# Codex Cross-Window Steering

Use this skill when Eddie wants the current Codex lane to guide another live Codex agent in a separate VS Code window, Codex Desktop window, or chat thread.

This skill is for steering external Codex lanes. It is not the same as spawning a subagent inside the current chat.

## Workflow

1. Identify the target lane:
   - window or app surface if visible
   - repo or task lane
   - active failure or steering goal
   - whether Eddie wants a paste-ready packet, clipboard handoff, or direct visible UI action
2. Build an authority packet before instructing the other agent:
   - Eddie's newest instruction
   - governing config or repo contract that must not drift
   - live local evidence
   - known degraded evidence
   - exact next action for the target agent
3. Separate evidence classes:
   - `confirmed`: directly observed local state, source docs, command output, or status page
   - `inferred`: likely cause based on confirmed signals
   - `degraded`: probes that failed or produced partial evidence
   - `blocked`: action requiring Eddie, missing tool, or external outage
4. Write a durable steering packet under:
   - `%USERPROFILE%\.codex\workstreams`
5. Put the short steering packet on the Windows clipboard when useful.
6. If direct UI steering is requested, use only a visible, narrow input path and do not reset or reload VS Code.
7. Report exactly what was prepared, where it was written, and what evidence backs it.

## Packet Contract

Every packet must include:

- target lane
- timestamp
- steering instruction
- confirmed evidence
- degraded or blocked evidence
- do-now list
- do-not-do list
- artifacts or commands the target agent should use
- acceptance condition

Use the helper script for deterministic packet creation:

```bash
python3 "$CODEX_HOME/skills/codex-cross-window-steering/scripts/write_steering_packet.py" \
  --title "Codex gpt-5.5 outage steering" \
  --target "VS Code Codex window" \
  --instruction "Preserve gpt-5.5/xhigh config; use local 9000/2337 rescue surfaces." \
  --confirmed "OpenAI status confirms Codex gpt-5.5 elevated errors." \
  --confirmed "Local config parity is clean." \
  --degraded "Collector hard-requires missing pwsh." \
  --do "Use local rescue surfaces while outage is active." \
  --dont "Do not silently downgrade model config." \
  --clipboard
```

## Guardrails

- Do not silently change `config.toml`, `MEMORY.md`, model selections, runtime modes, MCP routes, or ports as part of steering.
- Do not treat a clipboard packet as delivered to a separate agent unless Eddie pastes it or a visible UI action is confirmed.
- Do not use WSL loopback failures as authoritative Windows app health when Windows-side endpoint evidence is available.
- Do not broad-restart VS Code, Codex Desktop, or the STARFRAME stack unless Eddie explicitly requests that repair.
- Do not expose secrets, private prompt material, private repo details, or adult/private enclave data in a packet unless Eddie explicitly scopes it for the local target lane.
- Keep public-repo handoff text public-safe when the target lane is working on third-party or public PRs.

## Direct UI Action Boundary

Only perform direct UI action when Eddie asks for it explicitly or the target window and action are unambiguous.

Before direct UI action:

1. Confirm the target app/window.
2. Prepare the packet first.
3. Prefer paste-only input into the active target field.
4. Avoid window reloads, extension restarts, and focus-stealing automation.
5. After sending, verify visible acknowledgement or report that delivery is unconfirmed.

## Acceptance Evidence

Minimum accepted result:

- packet file path
- clipboard status if used
- target lane and intended action
- confirmed/degraded/blocker split

For direct UI steering, also include:

- visible target proof or Eddie confirmation
- whether the other agent acknowledged or only received the packet

## Best-Fit Companion Skills

- `$request-loopback-resume`
- `$codex-degraded-recovery`
- `$codex-config-self-maintenance`
- `$local-compute-usage`
- `$skill-trust-ledger`

## Scope Boundary

Use this skill only for cross-window or cross-thread Codex steering.

Do not use it for:

1. ordinary single-lane implementation work
2. public PR text unless paired with public-repo export controls
3. changing Codex config or runtime contracts
4. generic subagent spawning inside the current chat

## Loopback

If steering remains unresolved:

1. update or create a workstream state file
2. mark the lane as `blocked` only when the exact delivery blocker is known
3. preserve the packet path and next paste/action step
4. route back through the skill arbiter chain before trying a broader repair
