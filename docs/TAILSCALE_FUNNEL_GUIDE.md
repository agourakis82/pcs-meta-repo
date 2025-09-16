# Tailscale Funnel Setup Guide

Complete guide for setting up Tailscale funnel with your MCP server and custom domain `agourakis.med.br`.

## 🚀 Quick Start

Run the automated fix script:
```bash
chmod +x fix_tailscale_funnel.sh
./fix_tailscale_funnel.sh
```

## 📋 Manual Setup Steps

### 1. Prerequisites

- Tailscale installed and logged in
- MCP server running on port 8000
- Custom domain `agourakis.med.br` (optional)

### 2. Check Tailscale Status

```bash
# Check if Tailscale is running
tailscale status

# Get your Tailscale domain name (CORRECT SYNTAX)
tailscale status --json | jq -r .Self.DNSName

# Get your Tailscale IP
tailscale status --json | jq -r '.Self.TailscaleIPs[0]'
```

### 3. Configure Tailscale Serve (NEW SYNTAX)

**HTTPS (Recommended):**
```bash
# Configure serve for HTTPS on port 443
tailscale serve --https=443 8000
```

**HTTP (Alternative):**
```bash
# Configure serve for HTTP on port 80
tailscale serve --http=80 8000
```

### 4. Enable Tailscale Funnel (NEW SYNTAX)

**HTTPS:**
```bash
# Enable HTTPS funnel (NEW SYNTAX - NOT the old "funnel 443 on")
tailscale funnel --https=443 on
```

**HTTP:**
```bash
# Enable HTTP funnel
tailscale funnel --http=80 on
```

### 5. Verify Configuration

```bash
# Check serve status
tailscale serve status

# Check funnel status
tailscale funnel status
```

## 🌐 Custom Domain Setup

### DNS Configuration

To use your custom domain `agourakis.med.br`, create a CNAME record:

```
Type: CNAME
Name: agourakis.med.br
Value: [your-tailscale-domain].ts.net
```

Example:
```
Type: CNAME
Name: agourakis.med.br
Value: demetriospcs.tail21cbc4.ts.net
```

### Verification

After DNS propagation (can take up to 24 hours):
```bash
# Test custom domain
curl https://agourakis.med.br/health

# Test Tailscale domain
curl https://demetriospcs.tail21cbc4.ts.net/health
```

## 🔧 Common Commands

### Management Commands

```bash
# Stop funnel
tailscale funnel --https=443 off
tailscale funnel --http=80 off

# Reset serve configuration
tailscale serve reset

# Check status
tailscale serve status
tailscale funnel status
```

### Testing Commands

```bash
# Test local MCP server
curl http://localhost:8000/health

# Test Tailscale funnel
curl https://[your-domain].ts.net/health

# Test custom domain
curl https://agourakis.med.br/health
```

## ❌ Common Errors and Fixes

### Error: "invalid number of arguments (4)"

**Problem:** Using old syntax `tailscale funnel 443 on`

**Solution:** Use new syntax:
```bash
# OLD (WRONG)
sudo tailscale funnel 443 on

# NEW (CORRECT)
tailscale serve --https=443 8000
tailscale funnel --https=443 on
```

### Error: "No serve config"

**Problem:** Trying to enable funnel before configuring serve

**Solution:** Configure serve first:
```bash
# 1. Configure serve first
tailscale serve --https=443 8000

# 2. Then enable funnel
tailscale funnel --https=443 on
```

### Error: jq syntax error

**Problem:** Extra text in jq command

**Solution:**
```bash
# WRONG
tailscale status --json | jq -r .Self.DNSName demetriospcs.tail21cbc4.ts.net

# CORRECT
tailscale status --json | jq -r .Self.DNSName
```

### Error: "Funnel not available"

**Problem:** Funnel feature not enabled on your Tailscale account

**Solutions:**
1. Check if you have a paid Tailscale plan (required for some funnel features)
2. Try HTTP instead of HTTPS:
   ```bash
   tailscale serve --http=80 8000
   tailscale funnel --http=80 on
   ```

### Error: MCP server not responding

**Problem:** MCP server not running or not accessible

**Solutions:**
```bash
# Check if service is running
sudo systemctl status ragpp-mcp-server

# Start the service
sudo systemctl start ragpp-mcp-server

# Check if port is in use
sudo netstat -tlnp | grep :8000

# Test local connectivity
curl http://localhost:8000/health
```

## 🧪 Testing Your Setup

### Automated Test

Use the generated test script:
```bash
./test_mcp_funnel.sh
```

### Manual Testing

```bash
# 1. Test health endpoint
curl https://agourakis.med.br/health

# 2. Test API documentation
curl https://agourakis.med.br/docs

# 3. Test memory search (with authentication)
curl -X POST https://agourakis.med.br/memory/search \
  -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "max_results": 3}'
```

## 🔒 Security Considerations

### Firewall Configuration

```bash
# Allow Tailscale traffic
sudo ufw allow from 100.64.0.0/10 to any port 8000 comment "MCP via Tailscale"
```

### Authentication

Your MCP server uses Bearer token authentication:
```
Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo
```

## 📱 Access from Different Devices

Once configured, your MCP server will be accessible from any device in your Tailscale network:

- **Desktop:** https://agourakis.med.br
- **Mobile:** https://agourakis.med.br
- **Other computers:** https://agourakis.med.br

## 🔄 Troubleshooting Checklist

1. ✅ Tailscale installed and logged in
2. ✅ MCP server running on localhost:8000
3. ✅ Serve configured before funnel
4. ✅ Using new command syntax
5. ✅ DNS CNAME record created (for custom domain)
6. ✅ Firewall allows Tailscale traffic
7. ✅ Funnel feature available on your Tailscale plan

## 📞 Getting Help

If you continue having issues:

1. Check Tailscale logs: `sudo journalctl -u tailscaled -f`
2. Check MCP server logs: `sudo journalctl -u ragpp-mcp-server -f`
3. Verify network connectivity: `ping agourakis.med.br`
4. Test DNS resolution: `nslookup agourakis.med.br`

## 🎯 Final URLs

After successful setup:

- **Custom Domain:** https://agourakis.med.br
- **Tailscale Domain:** https://demetriospcs.tail21cbc4.ts.net
- **Health Check:** https://agourakis.med.br/health
- **API Docs:** https://agourakis.med.br/docs
- **Memory Search:** https://agourakis.med.br/memory/search

---

*This guide covers the new Tailscale serve/funnel syntax introduced in recent versions. The old syntax (`tailscale funnel 443 on`) is deprecated.*
