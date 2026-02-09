# REPO_B Strict Command Matrix

- Fast preflight: `pwsh -File tools/preflight.ps1 -Fast`
- Hardware strict preflight: `pwsh -File tools/preflight.ps1 -Hardware -ForceReal -repo_bOnly -VerboseOutput`
- Machine-readable preflight: `python tools/preflight.py`
- Doctor in strict mode: `repo_b_ONLY=1 repo_b_FORCE_REAL=1 REPO_B_INFERENCE_PROVIDER=repo_b_only python3 -m repo_b_repo_b_python_shim --doctor`

If strict commands cannot run in the current environment, report explicit "Run on target PC" follow-up steps.
