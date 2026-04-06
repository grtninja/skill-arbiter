# Canvas Debugging Reference

## Architecture Overview

```
Canvas Host (HTTP, port 18793) → Node Bridge (TCP, port 18790) → Node App (Mac/iOS/Android WebView)
```

The canvas host serves files from `canvasHost.root`. The node bridge relays canvas URLs to connected nodes. Nodes render content in a WebView.

## Bind Modes and URL Routing

| Bind Mode  | Server Binds To     | Canvas URL Uses            |
| ---------- | ------------------- | -------------------------- |
| `loopback` | 127.0.0.1           | localhost (local only)     |
| `lan`      | LAN interface       | LAN IP address             |
| `tailnet`  | Tailscale interface | Tailscale hostname         |
| `auto`     | Best available      | Tailscale > LAN > loopback |

The `canvasHostHostForBridge` is derived from `bridgeHost`. When bound to Tailscale, nodes receive URLs like `http://<tailscale-hostname>:18793/__openclaw__/canvas/<file>.html`.

Find your Tailscale hostname:

```bash
tailscale status --json | jq -r '.Self.DNSName' | sed 's/\.$//'
```

## URL Path Structure

The canvas host serves from the `/__openclaw__/canvas/` prefix (defined by `CANVAS_HOST_PATH`):

```
http://<host>:18793/__openclaw__/canvas/index.html      → ~/clawd/canvas/index.html
http://<host>:18793/__openclaw__/canvas/games/snake.html → ~/clawd/canvas/games/snake.html
```

## Common Issues

### White screen / content not loading

**Cause:** URL mismatch between server bind and node expectation.

1. Check server bind: `cat ~/.openclaw/openclaw.json | jq '.gateway.bind'`
2. Check what port canvas is on: `lsof -i :18793`
3. Test URL directly: `curl http://<hostname>:18793/__openclaw__/canvas/<file>.html`

**Solution:** Use the full hostname matching your bind mode, not localhost.

### "node required" error

Always specify `node:<node-id>` parameter in canvas actions.

### "node not connected" error

Node is offline. Use `openclaw nodes list` to find online nodes.

### Content not updating (live reload)

1. Check `liveReload: true` in `~/.openclaw/openclaw.json`
2. Ensure file is in the canvas root directory
3. Check for watcher errors in logs

## Configuration Example

```json
{
  "canvasHost": {
    "enabled": true,
    "port": 18793,
    "root": "~/clawd/canvas",
    "liveReload": true
  },
  "gateway": {
    "bind": "auto"
  }
}
```

## Tips

- Keep HTML self-contained (inline CSS/JS) for best results
- Use the default index.html as a test page (has bridge diagnostics)
- The canvas persists until you `hide` it or navigate away
- Live reload watches the root directory via chokidar and injects a WebSocket client into HTML files
- A2UI JSON push is WIP — use HTML files for now
