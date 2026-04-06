# Qwen Training Campaign Ops Checklist

Use this reference when Qwen Training Workbench campaigns or queue semantics change.

## Required Surfaces

1. campaign catalog config
2. campaign start API
3. queue/job state
4. dependency expansion and `requires_success_of` links
5. retry, cancel, and restart recovery behavior

## Failure Patterns

- named campaigns bypass the worker and call raw scripts directly
- dependency failures still trigger continuation batches
- restart recovery loses campaign ownership or queue state
- sister repos depend on undocumented queue or campaign fields
