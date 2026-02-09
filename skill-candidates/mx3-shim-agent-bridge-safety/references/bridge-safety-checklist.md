# Agent Bridge Safety Checklist

1. Default to `read_only` mode.
2. Use `controlled_write` only with explicit `allow_write=true` requests.
3. Keep `MX3_CONTINUE_APPLY_ENABLED=0` until reviewed diffs are ready.
4. Restrict write roots to the smallest practical paths.
5. Run local validation gates after bridge-assisted edits.
