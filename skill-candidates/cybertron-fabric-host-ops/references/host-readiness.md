# Host Readiness

Cybertron host readiness is valid only when all of the following are known:

1. WinRM listener state
2. RDP reachability
3. LM Studio model endpoint reachability
4. MeshGPT host-terminal health
5. VRM display readiness marker

## Status labels

- `ready`: the check succeeded.
- `blocked`: the check failed.
- `unknown`: the check was not provided to the helper script.

## Notes

- WinRM is the primary automation lane.
- RDP is break-glass only.
- VRM display readiness may be read from a local marker or configuration file when the display is not directly inspectable from the current host.
