# MeshGPT Gate Checklist

1. `ruff check .` passed.
2. `mypy meshgpt_node` passed or only pre-existing baseline issues remain.
3. Mesh selftest command completed with clear output.
4. Changes to policy/config files include rationale and docs sync.
5. No hardcoded secrets or endpoint values were introduced.
