# Cloudflare SSL/TLS Troubleshooting (Tunnels + Universal SSL)

Use this checklist when HTTPS fails (e.g., SSL handshake failure) for domains behind Cloudflare Tunnel.

## Quick Checks

- Universal SSL: Enabled (SSL/TLS > Edge Certificates)
- Certificate Status: "Active" for `agourakis.med.br` and `*.agourakis.med.br`
- Validation: No pending DCV; if CNAME setup, Cloudflare auto-validates. For TXT DCV, ensure `_acme-challenge.agourakis.med.br` TXT records match values provided.
- DNS Proxy: Orange-cloud ON for hostnames (proxied)
- TLS Mode: Full (strict) or Full; avoid Off/Flexible for tunnels
- TLS Version: Allow TLS 1.2+ (no need to force 1.3 if issues during issuance)
- mTLS/Access: Disabled for the hostname during validation/testing
- CAA Records: If present, allow `letsencrypt.org` and `pki.goog` (Google Trust Services)

## Tunnel Hostname Mapping

- Zero Trust > Networks > Tunnels > <your-tunnel> > Public Hostnames
  - `agourakis.med.br` -> <http://127.0.0.1:8080>
  - `mcp.agourakis.med.br` -> <http://127.0.0.1:8081>
- DNS > Records
  - `mcp` proxied (orange) CNAME to the tunnel UUID, or A/AAAA to Cloudflare edge (managed). Avoid grey-cloud (direct origin) for tunnels.

## Commands

Run these from your server or anywhere with `curl`, `dig`, `openssl`:

```bash
# Health over HTTPS
curl -I https://mcp.agourakis.med.br/health

# OpenAPI/schema quick checks
curl -s https://mcp.agourakis.med.br/actions/schema | jq -r .openapi
curl -s https://mcp.agourakis.med.br/openapi.json | head -n 5

# TLS handshake details
openssl s_client -servername mcp.agourakis.med.br -connect mcp.agourakis.med.br:443 -brief -showcerts </dev/null

# ACME TXT records (if using TXT DCV)
dig +short TXT _acme-challenge.agourakis.med.br @1.1.1.1

# DNS overview
dig +short mcp.agourakis.med.br A @1.1.1.1
Dig +short CNAME mcp.agourakis.med.br @1.1.1.1
```

## Common Fixes

- Toggle Universal SSL OFF then ON to force re-issuance
- Remove conflicting per-hostname certificates in Edge Certificates (keep Universal active)
- Temporarily disable: mTLS, Access, Require Modern TLS (if blocking issuance)
- Ensure no Page Rules/Transform Rules alter `Host` header for `mcp.*`
- Wait propagation: TXT/CNAME changes can take 5–15 minutes globally

## When It Works

- `curl -I https://mcp.agourakis.med.br/health` → 200 OK
- `openssl s_client` shows a valid cert chain for `*.agourakis.med.br` or `agourakis.med.br` issued by Google Trust Services (or Let’s Encrypt)

## After HTTPS Is Green

- Re-enable mTLS/Access if needed (allowlist ChatGPT ASN/IPs if required)
- Apply WAF and Rate Limits per `docs/CLOUDFLARE_SECURITY.md`
- Import the Actions schema URL in ChatGPT: `https://mcp.agourakis.med.br/actions/schema/noauth`
