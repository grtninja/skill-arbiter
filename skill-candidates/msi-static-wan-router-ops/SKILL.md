---
name: msi-static-wan-router-ops
description: Diagnose and tune Eddie's MSI router when it fronts an intentional Comcast static-IP handoff at `10.0.0.1`, including authenticated WebUI contract discovery, router-side ping/traceroute/nslookup, safe WAN DNS and LAN DHCP DNS changes, IPv4 and IPv6 verification, AI QoE mode changes, and rollback-first verification without resetting the router or disturbing the upstream gateway.
---

# MSI Static WAN Router Ops

Use this skill when the request involves Eddie's MSI GRAXE66 router, the internal Comcast gateway at `10.0.0.1`, or latency, DNS, QoE, or dual-stack IPv4 and IPv6 verification on the router without breaking the static handoff.

This skill is a candidate until it is audited and admitted.

## Non-negotiable contract

- Treat the Comcast gateway at `10.0.0.1` as an intentional static handoff, not accidental double NAT.
- Do not change the WAN addressing type, WAN IP, subnet, or gateway unless Eddie explicitly asks.
- Do not factory reset or reboot the router just to change DNS or QoE.
- Always capture before and after state and keep enough inputs to roll back.
- Prefer router-side diagnostics before workstation-only guesses.

## Auth contract

- Router UI: `http://192.168.1.1/index.html`
- Session salt: `GET /action=get_session`
- Token:
  1. `auth = SHA256(username + ":" + password)`
  2. `token = SHA256(auth_hex + salt)`
- Login: `POST /action=login` with headers `User`, `AuthToken`, and `ForceLogin=1` only when a web-admin slot is already occupied.

## Page and endpoint contract

- `dgnst.html` drives `/cgi-bin/diagnostics.cgi` for:
  - `ping`
  - `trace`
  - `nslookup`
  - `netstat`
- `tcpipwan.html` is the authoritative WAN and DNS form mapping.
- `tcpiplan.html` is the authoritative LAN DHCP handout mapping.
- `internet_ipv6.html` is the authoritative IPv6 mode, DHCPv6, and router-advertisement mapping.
- `basic_status.html` and `game_boost_mgls.html` carry the QoE mode contract.
- Read [references/router-contract.md](references/router-contract.md) when exact field names are needed.

## Workflow

1. Read the latest router workstream artifacts listed in [references/current-state.md](references/current-state.md).
2. Re-read the live router state before changes:
   - WAN static contract
   - current WAN DNS pair
   - current LAN DHCP `DNSServers`
   - current IPv6 WAN origin and gateway state
   - current LAN IPv6 origin and whether a delegated global prefix exists
   - current DHCPv6 and router-advertisement flags
   - current `Device.Acelink.Qoe.Mode`
3. Run router-side diagnostics first:
   - `nslookup` for `api.openai.com`, `chatgpt.com`, and `auth.openai.com`
   - `trace` for the target edge and at least one regional baseline
   - `ping` for `10.0.0.1`, OpenAI edge, and candidate DNS targets
   - when IPv6 is in scope, check whether the router can resolve AAAA records and whether IPv6 diagnostics succeed or return `ERROR`
4. Only then evaluate changes:
   - WAN DNS pair
   - LAN DHCP DNS handout
   - IPv6 WAN mode (`autoconfig`, `link_local`, `static`, `pppoe`, `6to4`)
   - DHCP-PD, DHCPv6, and RA settings
   - QoE mode (`ai`, `gaming`, `streaming`, `wfh`, `qos`)
5. For edits, post the full relevant form contract, not partial guessed fields.
6. Apply one change class at a time and verify immediately.
7. Roll back if the intended surface gets worse or the commit does not stick.

## Known good state from 2026-04-22

- WAN static handoff remained:
  - `10.0.0.134/24`
  - gateway `10.0.0.1`
- WAN DNS pair:
  - primary `1.1.1.1`
  - secondary `9.9.9.9`
- LAN DHCP DNS handout:
  - `1.1.1.1,9.9.9.9`
- QoE mode:
  - `gaming`

## Known dual-stack finding from 2026-04-22

- IPv4 is healthy on this lane.
- The MSI was initially configured for IPv6 WAN origin `WellKnown`, which this UI treats as `link_local`, not real autoconfiguration.
- The router was safely corrected to `AutoConfigured`, but native IPv6 still did not receive a usable gateway or delegated LAN prefix.
- The router showed:
  - WAN-side global IPv6 visibility
  - no IPv6 default gateway
  - no delegated LAN global prefix
  - clients with link-local IPv6 only
- `internet_ipv6.html` exposed the safe candidate repair path:
  - switch WAN mode from `link_local` to `autoconfig`
  - keep LAN DHCP-PD intent enabled
  - preserve RA and DHCPv6 settings unless measurement proves a different policy is needed
- Do not treat a good Boston or Xfinity speed-test result as proof that IPv6 is healthy.

Read [references/current-state.md](references/current-state.md) for artifact paths and measured baselines.

## Evidence contract

Every pass should leave:

- exact before and after artifact paths
- live router fields read
- router-side ping, traceroute, or nslookup output or a parsed summary
- explicit IPv4 and IPv6 verdicts
- whether rollback was needed
- any workstation-side timing used to confirm user-visible effect

## MCP upgrade path

If the router becomes a repeated surface, wrap the authenticated HTTP flow in a local MCP instead of introducing browser automation first. Preserve the same rollback-first contract and field-level reads from [references/router-contract.md](references/router-contract.md).

## Loopback

If the router contract changes or a page disappears:

1. Re-fetch the live page modules.
2. Re-map the exact `flash.cgi` or `diagnostics.cgi` fields.
3. Update the skill references before trusting stale selectors.
