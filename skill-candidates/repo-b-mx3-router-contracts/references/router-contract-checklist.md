# Router Contract Checklist

Use this checklist before completing MX3 router-profile changes.

## Required checks

1. `tests/test_model_router_capabilities.py` passes.
2. Router health endpoint reports both profile and effective policy.
3. Inference response payload includes the active network profile.
4. Profile aliases produce expected route mode:
   - `gaming` -> low-latency bias
   - `streaming` -> stability bias
   - `wfh` -> primary host bias
   - `traditional_qos` -> conservative/quality bias
   - `ai_auto` -> default adaptive behavior

## Evidence to capture

- Test output (pass/fail counts)
- Example health response JSON
- Example inference response JSON
- Any policy override env vars used in the run
