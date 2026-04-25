# Baseline Targets

## Local handoff truth

- MSI router: `192.168.1.1`
- Comcast internal gateway: `10.0.0.1`

## OpenAI and Cloudflare targets

- `api.openai.com`
- `chatgpt.com`
- `auth.openai.com`
- `cdn.oaistatic.com`
- direct edge examples seen on 2026-04-22:
  - `172.66.0.243`
  - `162.159.140.245`
  - `1.1.1.1`
- IPv6-capable targets used in the dual-stack lane:
  - `chatgpt.com`
  - `2606:4700:4700::1111`
  - `2001:4860:4860::8888`

## Regional baseline targets

- `mit.edu`
- Providence fallback candidates only when needed:
  - use a real host in that geography
  - verify the actual route instead of assuming it is shorter

## Resolver candidates used in the 2026-04-22 lane

- Comcast:
  - `75.75.75.75`
  - `75.75.76.76`
- Cloudflare:
  - `1.1.1.1`
  - `1.0.0.1`
- Quad9:
  - `9.9.9.9`
  - `149.112.112.112`
- OpenDNS:
  - `208.67.220.220`
  - `208.67.222.222`
- Google:
  - `8.8.8.8`
  - `8.8.4.4`

## Path labels that mattered in the live lane

These labels helped classify the route:

- `mashpee.ma.boston.comcast.net`
- `needham.ma.boston.comcast.net`
- `woburn.ma.boston.comcast.net`
- `chelmsfdrdc2.ma.boston.comcast.net`
- `newark.nj.ibone.comcast.net`
- Akamai `icn` or `ien` hops

## Interpretation notes

- Stable `192.168.1.1` and `10.0.0.1` latency means the big spread is upstream.
- Anycast DNS wins should be judged by repeated query time and trace path, not just ping.
- MIT is valuable here because it shows how a geographically close destination can still ride a long provider path.
- A good Xfinity or Boston speed test is supporting evidence for IPv4 health, not proof that IPv6 is working.
- If the router can resolve AAAA but clients have no global IPv6 and no IPv6 default route, classify the lane as IPv4-healthy and IPv6-broken.
