# Current State

These artifacts capture the proven router state from the 2026-04-22 lane:

- `%USERPROFILE%\.codex\workstreams\router-dns-change-20260422-085549.json`
- `%USERPROFILE%\.codex\workstreams\router-lan-dns-handout-20260422-085900.json`
- `%USERPROFILE%\.codex\workstreams\router-qoe-mode-20260422-090334.json`
- `%USERPROFILE%\.codex\workstreams\stale-process-culprit-map-SOUNDWAVE3-20260422-090556-router-latency-lane.json`
- `%USERPROFILE%\.codex\workstreams\router-static-wan-latency-20260422.quest.json`
- `%USERPROFILE%\.codex\workstreams\router-static-wan-latency-20260422.resume.json`

## Proven state

- Comcast static gateway remains at `10.0.0.1`
- MSI WAN static IP remains `10.0.0.134/24`
- Router WAN DNS pair is `1.1.1.1` then `9.9.9.9`
- Router LAN DHCP DNS handout is `1.1.1.1,9.9.9.9`
- Router QoE mode is `gaming`

## Dual-stack verdict from 2026-04-22

- IPv4 is healthy end to end.
- The MSI IPv6 page was initially configured as WAN `link_local` and was safely corrected to `autoconfig`:
  - before: `Device.IP.Interface.2.IPv6Address.1.Origin = WellKnown`
  - after: `Device.IP.Interface.2.IPv6Address.1.Origin = AutoConfigured`
  - LAN stayed `Device.IP.Interface.1.IPv6Address.1.Origin = WellKnown` to preserve DHCP-PD intent
- DHCPv6 and RA were enabled on the LAN side, but there was:
  - no usable IPv6 default gateway
  - no LAN global IPv6 prefix
  - no client global IPv6 address on `Ethernet 5`
- Router-side DNS could resolve AAAA for `chatgpt.com`, but workstation-side IPv6 transport was still absent.
- Router-side IPv6 ping attempts returned `ERROR`.
- Xfinity speed-test throughput looked healthy, but that did not prove IPv6 was working.

## What was improved

- The router stopped handing out blank DHCP DNS values.
- The workstation and clients no longer need to depend on the router forwarder path by default.
- Router-side OpenAI edge ping kept the same average but reduced the recorded max spike after the QoE switch.

## What remains true

- The biggest latency spread is still upstream pathing, not the MSI LAN handoff.
- MIT remains a useful baseline because the wire path detours far beyond physical Cape-to-Cambridge distance.
- IPv6 requires a separate verification lane from IPv4 throughput and ping.
