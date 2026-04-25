---
name: openclaw-slash-runtime-parity
description: Validate OpenClaw-style slash commands on the live VRM Sandbox runtime with 5-minute patience, and return concrete chat, RAG, and TTS evidence instead of vague status claims.
---

# OpenClaw Slash Runtime Parity

Use this skill when `/status`, `/tasks`, `/help`, `/tts`, or similar command turns need to be verified on the running local stack with deterministic evidence.

## Workflow

1. Run the probe script against live runtime chat routes.
2. Use explicit slash commands as input vectors.
3. Keep action timeout at least 300 seconds for command turns.
4. Capture output from:
   - `/runtime/chat/send` response body
   - `/runtime/chat/window-state` message/speak status
   - latest VRM session log event window
5. Report command-level outcomes:
   - assistant reply presence
   - reply preview and length
   - RAG retrieval events
   - TTS terminal event (`tts.play`, `tts.error`, `tts.emoji_only`, etc.)
6. If parity fails, route directly into code repair for the exact lane that failed.

## Canonical Command

```powershell
powershell -ExecutionPolicy Bypass -File scripts/probe_slash_runtime.ps1 `
  -Commands '/status','/tasks','/help','/tts on' `
  -TimeoutSec 300
```

## Guardrails

- Do not treat GPU activity as proof of reply completion.
- Do not treat one slash command passing as parity for all slash commands.
- Do not claim TTS success unless a terminal TTS event is present for that turn.
- Do not bypass RAG evidence checks for slash-command turns.

## Scope Boundary

Use this skill only for live slash-command runtime parity checks and evidence capture.

For static contract patching, route through `$openclaw-runtime-contract-guard`.
