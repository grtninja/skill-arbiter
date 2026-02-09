# WSL Hybrid Boundaries

- Windows hosts all REPO_B hardware-facing execution.
- WSL hosts auxiliary services only (ComfyUI, helper model services).
- Hardware failures in strict mode are not treated as WSL networking issues.
- Keep connector URLs loopback-local from Windows perspective.
