# Thin-Waist Checklist

1. `/v1/models`, `/v1/chat/completions`, and `/v1/vision` respond with stable JSON contracts.
2. `/api/jobs` async flow returns deterministic state progression.
3. `/api/resources` reflects current service bind metadata.
4. Route decisions remain in router policy, not transport adapters.
