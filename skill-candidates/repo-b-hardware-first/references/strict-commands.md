# REPO_B Strict Command Matrix

- Fast preflight: `pwsh -File tools/preflight.ps1 -Fast`
- Hardware strict preflight: `pwsh -File tools/preflight.ps1 -Hardware -ForceReal -MemryxOnly -VerboseOutput`
- Machine-readable preflight: `python tools/preflight.py`
- Doctor in strict mode: `$env:REPO_B_ONLY=1; $env:REPO_B_FORCE_REAL=1; $env:REPO_B_INFERENCE_PROVIDER=repo_b_only; python -m memryx_mx3_python_shim --doctor`

If strict commands cannot run in the current environment, report explicit "Run on target PC" follow-up steps.
