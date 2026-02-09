# MX3 Strict Command Matrix

- Fast preflight: `pwsh -File tools/preflight.ps1 -Fast`
- Hardware strict preflight: `pwsh -File tools/preflight.ps1 -Hardware -ForceReal -MemryxOnly -VerboseOutput`
- Machine-readable preflight: `python tools/preflight.py`
- Doctor in strict mode: `MEMRYX_ONLY=1 MEMRYX_FORCE_REAL=1 MX3_INFERENCE_PROVIDER=mx3_only python3 -m memryx_mx3_python_shim --doctor`

If strict commands cannot run in the current environment, report explicit "Run on target PC" follow-up steps.
