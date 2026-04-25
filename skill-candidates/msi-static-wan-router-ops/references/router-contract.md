# Router Contract

## Live hardware surface

- Router: MSI GRAXE66 class UI
- Firmware observed on 2026-04-22: `753678`
- Router UI: `http://192.168.1.1`
- LAN IP: `192.168.1.1`
- WAN static handoff:
  - IP `10.0.0.134`
  - mask `255.255.255.0`
  - gateway `10.0.0.1`

## Login flow

1. `GET /index.html`
2. `GET /action=get_session`
3. Compute:
   - `auth = SHA256(username + ":" + password)`
   - `token = SHA256(auth_hex + salt)`
4. `POST /action=login` with headers:
   - `User`
   - `AuthToken`
   - optional `ForceLogin=1`

## Diagnostics contract

The diagnostics page uses `/cgi-bin/diagnostics.cgi`.

- Start a diagnostic:
  - `/cgi-bin/diagnostics.cgi?method=ping&ping_ip_addr=<ip>&pkt_size=64&cnt=4`
  - `/cgi-bin/diagnostics.cgi?method=trace&route_ip_addr=<host-or-ip>`
  - `/cgi-bin/diagnostics.cgi?method=nslookup&nslookup_addr=<host>`
- Poll results:
  - `/cgi-bin/diagnostics.cgi?result=ping`
  - `/cgi-bin/diagnostics.cgi?result=trace`
  - `/cgi-bin/diagnostics.cgi?result=nslookup`

Results end with `END`.

## WAN form keys

These are the important `tcpipwan.html` mappings used in the live lane:

- `Device.Acelink.IP.Interface.2.IPv4Address.1.AddressingType`
- `Device.IP.Interface.2.IPv4Address.1.IPAddress`
- `Device.IP.Interface.2.IPv4Address.1.SubnetMask`
- `Device.Acelink.IP.Interface.2.IPv4Address.1.GatewayIPAddress`
- `Device.DNS.Client.Server.1.DNSServer`
- `Device.DNS.Client.Server.2.DNSServer`
- `Device.DNS.Client.Server.1.Enable`
- `Device.DNS.Client.Server.2.Enable`
- `Device.IP.Interface.2.MaxMTUSize`
- `Device.Acelink.Ethernet.2.CloneMACAddr`
- `Device.Ethernet.Link.2.Name`
- `Device.Ethernet.Link.1.Name`
- `apply_flag=wan`

Do not post guessed partial WAN fields. Post the full relevant contract.

## IPv6 form keys

These are the important `internet_ipv6.html` mappings used in the live lane:

- `Device.IP.Interface.2.IPv6Address.1.Origin`
- `Device.Acelink.IP.Interface.2.IPv6Address.1.Origin`
- `Device.IP.Interface.2.IPv6Address.1.IPAddress`
- `Device.IP.Interface.2.IPv6Prefix.1.Enable`
- `Device.IP.Interface.2.IPv6Prefix.1.Prefix`
- `Device.Acelink.IP.Interface.2.IPv6Address.1.GatewayIPAddress`
- `Device.IP.Interface.1.IPv6Address.1.Origin`
- `Device.IP.Interface.1.IPv6Address.1.IPAddress`
- `Device.IP.Interface.1.IPv6Prefix.1.Enable`
- `Device.IP.Interface.1.IPv6Prefix.1.Prefix`
- `Device.DNS.Client.Server.3.Enable`
- `Device.DNS.Client.Server.3.DNSServer`
- `Device.DNS.Client.Server.4.Enable`
- `Device.DNS.Client.Server.4.DNSServer`
- `Device.DHCPv6.Server.Pool.1.Enable`
- `Device.RouterAdvertisement.InterfaceSetting.1.Enable`
- `Device.RouterAdvertisement.InterfaceSetting.1.AdvManagedFlag`
- `Device.RouterAdvertisement.InterfaceSetting.1.AdvOtherConfigFlag`
- `Device.Acelink.DHCPv6.Server.Pool.1.IPRange`
- `Device.Acelink.DHCPv6.Server.Pool.1.Lifetime`
- `Device.Acelink.RouterAdvertisement.InterfaceSetting.1.Lifetime`
- `Device.PPP.Interface.1.IPv6CPEnable`
- `Device.PPP.Interface.2.IPv6CPEnable`
- `Device.Acelink.PPP.1.IPv6AddressMode`
- `Device.Acelink.PPP.1.IPv6Address`
- `Device.Acelink.IPv6toIPv4.RelayServer`
- `Device.Acelink.IPv6toIPv4.LANIPv6Address`
- `apply_flag=ipv6`

Important mode meanings from the live page contract:

- `AutoConfigured` is the real autoconfig path.
- `WellKnown` maps to the UI's `link_local` mode.
- LAN `WellKnown` is how the UI expresses DHCP-PD for the LAN side.

## LAN DHCP handout keys

These are the important `tcpiplan.html` mappings used in the live lane:

- `Device.IP.Interface.1.IPv4Address.1.IPAddress`
- `Device.IP.Interface.1.IPv4Address.1.SubnetMask`
- `Device.DHCPv4.Server.Enable`
- `Device.DHCPv4.Server.Pool.1.MinAddress`
- `Device.DHCPv4.Server.Pool.1.MaxAddress`
- `Device.DHCPv4.Server.Pool.1.LeaseTime`
- `Device.DHCPv4.Server.Pool.1.IPRouters`
- `Device.DHCPv4.Server.Pool.1.DNSServers`
- `Device.DHCPv4.Server.Pool.1.DomainName`
- `Device.DHCPv4.Server.Pool.1.SubnetMask`
- `apply_flag=lan,openvpn`

## QoE mode keys

The dashboard and game-center pages exposed:

- `Device.Acelink.Qoe.Enable`
- `Device.Acelink.Qoe.Mode`
- `Device.Acelink.Qoe.LastMode`
- `Device.Acelink.Qoe.PolicyConfirmation`
- `Device.Acelink.Qos.Enable`
- `Device.Acelink.BandwidthLimiter.Enable`

Known mode strings:

- `ai`
- `gaming`
- `streaming`
- `wfh`
- `qos`

Dashboard apply flag for AI QoE modes:

- `apply_flag=msi_qoe`
