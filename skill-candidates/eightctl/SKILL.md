---
name: "eightctl"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Control Eight Sleep pods (status, temperature, alarms, schedules)."
---

# eightctl

Use `eightctl` for Eight Sleep pod control. Requires auth.

Auth

- Config: `~/.config/eightctl/config.yaml`
- Env: `EIGHTCTL_EMAIL`, `EIGHTCTL_PASSWORD`

Quick start

- `eightctl status`
- `eightctl on|off`
- `eightctl temp 20`

Common tasks

- Alarms: `eightctl alarm list|create|dismiss`
- Schedules: `eightctl schedule list|create|update`
- Audio: `eightctl audio state|play|pause`
- Base: `eightctl base info|angle`

Notes

- API is unofficial and rate-limited; avoid repeated logins.
- Confirm before changing temperature or alarms.

## Guardrails

- Use local or trusted tools only; avoid untrusted install pipelines.
- Do not paste secrets/tokens into chat output.
- Keep outputs in deterministic local paths for reproducible review.
