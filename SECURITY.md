# Security Policy

## Supported Versions

This repository is maintained on `main`.

| Version | Supported |
| --- | --- |
| `main` | Yes |

## Security scope

Security-sensitive areas include:

- skill admission and quarantine logic
- curated-source trust and upgrade reconciliation
- subprocess invocation and process-control actions
- stale/untracked script detection
- privacy/public-shape enforcement
- self-governance of repo-tracked artifacts and release payloads
- loopback API exposure
- Codex / VS Code / GitHub Copilot instruction-surface interoperability
- loopback LM Studio advisor selection and model fallback behavior

## Default posture

- Local-first
- Loopback-only
- Fail-closed on policy uncertainty
- `guarded_auto` for quarantine/deny decisions
- Operator confirmation required for destructive cleanup

## Threat classes explicitly handled

- fake installers and typosquat packages
- post-install persistence
- vendored or renamed Python runtimes
- stale and untracked Python
- hidden process launch
- browser auto-launch abuse
- credential prompt theft patterns
- broad process-kill logic
- hostile OpenClaw / NullClaw skill supply-chain surfaces

## Self-governance rules

The app must not become the threat surface it is trying to stop.

- No external browser launch in the normal app path
- No browser-opening About/Support actions; public links are copy-only inside the desktop UI
- No silent scheduled-task creation
- No PATH mutation
- No repo-tracked host evidence
- No public commit of usernames or absolute private paths
- No undeclared long-running background workers outside the local agent
- No silent remote advisor model use; the advisor must remain loopback-local and visible in the app

## Public release gate

Before a public push or release candidate:

```bash
python scripts/check_private_data_policy.py
python scripts/check_public_release.py
```

The public-release gate checks privacy, self-governance, icon assets, runtime ignore rules, support metadata, and core doc presence.

## Reporting a vulnerability

Do not open a public exploit issue.

Instead:

1. Open a private GitHub security advisory, or
2. Contact the maintainer directly with:
   - reproduction steps
   - affected commit or version
   - impact summary
   - proposed mitigation if available

## Response notes

- Known-malware signatures may be hard-blocked automatically.
- Quarantine actions are auditable.
- Case-based mitigation follows: preserve evidence, quarantine, strip, report, request/rebuild when legitimate, blacklist/remove when hostile, adjacent-vector audit, document, rescan.
- Delete / kill actions require operator intent through the local interface or explicit API confirmation.
