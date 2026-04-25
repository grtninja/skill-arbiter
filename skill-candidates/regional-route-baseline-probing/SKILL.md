---
name: regional-route-baseline-probing
description: Probe physical-distance versus wire-path latency from Eddie's Provincetown and Cape-style Comcast uplink using workstation-side and router-side baselines such as MIT, Providence, OpenAI, Cloudflare, and DNS anycast routes to separate local handoff issues from upstream or CDN detours, including dual-stack IPv4 and IPv6 verification.
---

# Regional Route Baseline Probing

Use this skill when the request is about regional path quality, wire distance versus physical distance, Cape or Boston pathing, MIT baseline probes, Providence fallback reasoning, or choosing the least-bad anycast DNS route for Eddie's line.

This skill is a candidate until it is audited and admitted.

## Core rules

- Always pair workstation-side probes with router-side probes.
- Use `192.168.1.1` and `10.0.0.1` as the local handoff truth before blaming the wider path.
- Treat IPv4 path quality and IPv6 path viability as separate measurements.
- Use MIT as a Boston-area baseline when Eddie is reasoning about physical distance versus actual wire route.
- Use Providence as a fallback baseline when southbound routing is in scope, but verify the real route rather than assuming the shortest map path wins.
- Treat DNS anycast as route selection by measurement, not by city-name guesswork.

## Workflow

1. Confirm the local handoff first:
   - workstation to `192.168.1.1`
   - router to `10.0.0.1`
2. Run router-side diagnostics:
   - `nslookup`
   - `trace`
   - `ping`
3. Run workstation-side probes:
   - `Resolve-DnsName`
   - `Resolve-DnsName -Type AAAA`
   - `Test-Connection`
   - `Test-Connection -IPv6` when a real IPv6 target exists
   - `tracert -d`
   - `curl -w` timing for real HTTPS targets
   - `curl -6` only when the client actually has a usable IPv6 address and route
4. Compare at least three route classes:
   - OpenAI or Cloudflare edge
   - MIT or another Boston-area baseline
   - candidate DNS anycast resolvers
5. Classify the spread:
   - local handoff issue
   - gateway handoff issue
   - upstream Comcast path issue
   - CDN or anycast placement issue
   - missing or partial IPv6 service
6. Recommend resolver or QoE changes only when the measured path supports them.

## Known observations from 2026-04-22

- Router to `10.0.0.1` stayed around `0.7-2.1 ms`, which ruled out the MSI LAN side as the main jitter source.
- OpenAI's Cloudflare edge stayed on the shorter Massachusetts-facing path.
- MIT still detoured through a much longer wire path via Newark and New York Akamai infrastructure, which proved the physical-distance mismatch point.
- A healthy speed test to Boston did not prove IPv6 was working.
- The live dual-stack check showed an IPv4-healthy but IPv6-broken client path: no client global IPv6, no IPv6 default route, and only link-local client addressing.

Read [references/baseline-targets.md](references/baseline-targets.md) for exact targets and interpretation hints.

## Evidence contract

Every pass should leave:

- the targets tested
- router-side and workstation-side results
- min, avg, and max where available
- notable hop owner labels
- a short classification of where the latency spread actually starts

## Loopback

If the path looks different from the recorded 2026-04-22 baseline:

1. re-run the local handoff probes
2. re-run the router-side trace to the target
3. update the quest artifact before making new tuning claims
