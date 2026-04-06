# Cross-App Queue Backpressure Checklist

- Confirm the canonical queue owner for each surface.
- Check retry, cancel, and interrupted-job behavior.
- Preserve heavy-lane mutual exclusion rules.
- Verify UI queue state against backend state.
- Record the bounded queue proof used for closure.
