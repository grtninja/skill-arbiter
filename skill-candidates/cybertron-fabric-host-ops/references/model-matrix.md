# Canonical Model Matrix

This skill validates the canonical remote-subagent model set for Cybertron-side host readiness.

| Role | Canonical model |
| --- | --- |
| Primary general | `huihui-qwen3.5-4b-abliterated` |
| Instruct overflow | `huihui-qwen3-4b-instruct-2507-abliterated` |
| General vision | `huihui-qwen3-vl-4b-instruct-abliterated` |
| Coder | `qwen2.5-coder-1.5b-instruct-abliterated` |
| Embeddings | `text-embedding-nomic-embed-text-v1.5` |

## Validation rule

- Do not introduce alternate aliases for the same model family.
- Do not let host-specific labels replace the canonical IDs above.
- Treat `text-embedding-nomic-embed-text-v1.5-embedding` as an LM Studio alias for the canonical embeddings lane.
- `huihui-gpt-oss-20b-abliterated-v2` stays local on `Shockwave3`; it is not a required Cybertron host-readiness model.
- `huihui-qwen3.5-2b-abliterated` and `huihui-qwen3.5-0.8b-abliterated` remain optional staged lanes rather than required loaded-host probes.
