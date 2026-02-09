# Security Policy

## Supported Versions

This repository is currently maintained on the `main` branch only.

| Version | Supported |
| --- | --- |
| `main` | Yes |

## Reporting a Vulnerability

If you discover a security issue, please do not open a public issue with exploit details.

Instead:

1. Open a private security advisory on GitHub (preferred), or
2. Contact the maintainer directly and include:
   - clear reproduction steps
   - impact assessment
   - affected commit/version
   - any proposed fix

You can expect acknowledgment within 5 business days.

## Scope Notes

- This project is a local automation utility and is not a hosted service.
- No API keys are required for normal operation.
- Security-sensitive areas include filesystem mutation, subprocess invocation, and skill source trust.
