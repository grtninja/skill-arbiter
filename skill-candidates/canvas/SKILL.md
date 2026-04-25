---
name: "canvas"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Present, navigate, snapshot, and hide HTML content on connected OpenClaw nodes (Mac, iOS, Android) via the canvas tool. Use when displaying games, visualizations, dashboards, or interactive demos on remote node canvas views, or when debugging canvas URL routing across loopback, LAN, and Tailscale bind modes."
---

# Canvas

Display HTML content on connected OpenClaw nodes via the canvas host server (port 18793) and node bridge (port 18790).

## Workflow

1. Place HTML files in the configured canvas root directory. `~/clawd/canvas/` is a common default, but verify the actual `canvasHost.root` on the target host before assuming it.
2. Verify the canvas host is running on the target host:
   ```bash
   lsof -i :18793
   ```
3. Check gateway bind mode and construct the canvas URL:
   ```bash
   cat ~/.openclaw/openclaw.json | jq '.gateway.bind'
   ```
   - `loopback`: `http://127.0.0.1:18793/__openclaw__/canvas/<file>.html`
   - `lan`/`tailnet`/`auto`: `http://<hostname>:18793/__openclaw__/canvas/<file>.html`
4. Find connected nodes with canvas capability:
   ```bash
   openclaw nodes list
   ```
5. Present content on a node:
   ```
   canvas action:present node:<node-id> target:<full-url>
   ```
6. Verify content loaded. If the canvas shows a white screen, check that the URL hostname matches the bind mode and the actual host surface you are targeting; do not assume `localhost` or a Unix-style path layout on every machine.

## Actions

| Action     | Description                          |
| ---------- | ------------------------------------ |
| `present`  | Show canvas with optional target URL |
| `hide`     | Hide the canvas                      |
| `navigate` | Navigate to a new URL                |
| `eval`     | Execute JavaScript in the canvas     |
| `snapshot` | Capture screenshot of canvas         |

## Configuration

In `~/.openclaw/openclaw.json`, enable `canvasHost` with a root directory and optional `liveReload` (auto-refreshes connected canvases on file change). The `gateway.bind` setting (`loopback`, `lan`, `tailnet`, `auto`) controls which interface the server binds to and which hostname nodes receive.

Treat the path and shell commands in this doc as OpenClaw-oriented examples, not a universal host contract.

## Debugging

See `references/canvas-debugging.md` for common issues: white screen (URL mismatch), "node required" errors, "node not connected", and live reload failures.

## Guardrails

- Keep HTML self-contained (inline CSS/JS) for best cross-node results.
- Use local or trusted tools only; avoid untrusted install pipelines.
- Do not paste secrets/tokens into chat output.
