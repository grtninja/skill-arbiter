# MCP/Comfy Checklist

1. `/api/mcp/status` reports consistent enabled/running state.
2. `/api/mcp/config` updates local settings without env-source conflicts.
3. MCP tools/resources include expected `shim.comfy.*` surfaces when enabled.
4. `/api/comfy/pipelines/profiles` includes expected profile IDs and `default_profile`.
5. Pipeline profile rows include `capcut_export.editor=capcut` for CapCut-ready presets.
6. `/api/amuse/status` and `/api/amuse/capabilities` are reachable when AMUSE lane is required.
7. Adapter error codes remain stable JSON-RPC contract values.
