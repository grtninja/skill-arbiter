# Contributing

## Development Setup

Requirements:

- Python 3.10+
- Git
- Windows host (for realistic `rg.exe` process sampling)

Quick checks:

```bash
python3 --version
python3 scripts/arbitrate_skills.py --help
python3 -m py_compile scripts/arbitrate_skills.py
```

## Pull Requests

Before opening a PR:

1. Keep changes focused and scoped.
2. Update docs (`README.md`, `SKILL.md`, or `references/`) if behavior changes.
3. Run the quick checks above.
4. Include rationale and risk notes in the PR description.

## Security

- Do not commit secrets, tokens, credentials, or private keys.
- If you identify a vulnerability, follow `SECURITY.md`.
