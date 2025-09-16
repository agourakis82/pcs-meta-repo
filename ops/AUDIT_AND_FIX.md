# Production Infrastructure Audit & Fix Plan
## PCS Meta Repo - Cloudflare Tunnel + Nginx Internal Architecture

**Engineer:** Senior SRE/DevOps  
**Date:** 2025-09-13  
**Scope:** Production-ready config for www.agourakis.med.br + mcp.agourakis.med.br  

---

## 🎯 **Architecture Overview**

```
Internet → Cloudflare Edge → Cloudflare Tunnel → Nginx (Internal HTTP) → FastAPI/Uvicorn
         (TLS Termination)   (Outbound Only)     (127.0.0.1:8440/8480)   (127.0.0.1:8000)
```

### Variables & Constants
```bash
ORG_DOMAIN="agourakis.med.br"
WWW_HOST="www.agourakis.med.br"
MCP_HOST="mcp.agourakis.med.br"
WWW_PORT=8440
MCP_PORT=8480
CLOUDFLARED_TUNNEL_NAME="agourakis"
CLOUDFLARED_UUID="REPLACE_WITH_REAL_UUID"
NGINX_USER="www-data"
```

---

## 📋 **AUDIT CHECKLIST**

### 1. **Cloudflare Tunnel Audit**

#### 1.1 Verify Tunnel Status
```bash
# Check if cloudflared is running
sudo systemctl status cloudflared
cloudflared tunnel list
cloudflared tunnel info ${CLOUDFLARED_TUNNEL_NAME}

# Expected: "ACTIVE" status, correct UUID
```

#### 1.2 Verify Tunnel Configuration
```bash
# Check current config
sudo cat /etc/cloudflared/config.yml
ls -la /etc/cloudflared/

# Expected: Valid ingress rules, correct credentials file
```

#### 1.3 Check Tunnel Connectivity
```bash
# Test tunnel connectivity
cloudflared tunnel run --dry-run ${CLOUDFLARED_TUNNEL_NAME}
sudo journalctl -u cloudflared -f --no-pager | head -20

# Expected: No connection errors, successful registration
```

### 2. **DNS Configuration Audit**

#### 2.1 Verify DNS Records
```bash
# Check DNS resolution
dig +short ${WWW_HOST}
dig +short ${MCP_HOST}
dig +short ${ORG_DOMAIN}

# Expected: Cloudflare IPs (104.21.x.x, 172.67.x.x)
```

#### 2.2 Verify Cloudflare Proxy Status
```bash
# Check if domains are proxied (orange cloud)
nslookup ${WWW_HOST}
nslookup ${MCP_HOST}

# Expected: Cloudflare IPs, not origin server IPs
```

#### 2.3 Test SSL/TLS from Edge
```bash
# Test edge SSL certificates
openssl s_client -connect ${WWW_HOST}:443 -servername ${WWW_HOST} </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer
openssl s_client -connect ${MCP_HOST}:443 -servername ${MCP_HOST} </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer

# Expected: Cloudflare certificates, not origin certs
```

### 3. **Nginx Internal Configuration Audit**

#### 3.1 Check Current Nginx Status
```bash
# Verify nginx is running
sudo systemctl status nginx
sudo nginx -t
sudo nginx -T | grep -E "(listen|server_name)" | head -10

# Expected: Syntax OK, test successful
```

#### 3.2 Verify Internal Ports Availability
```bash
# Check if target ports are available
sudo netstat -tulpn | grep -E ":8440|:8480"
sudo ss -tulpn | grep -E ":8440|:8480"

# Expected: Ports should be free for nginx to bind
```

#### 3.3 Check Nginx User Permissions
```bash
# Verify nginx user exists and has correct permissions
id ${NGINX_USER}
sudo -u ${NGINX_USER} -s /bin/bash -c "echo 'OK'"

# Expected: User exists, can execute commands
```

### 4. **FastAPI/Uvicorn Backend Audit**

#### 4.1 Verify Backend Service
```bash
# Check if ragpp service is running on port 8000
sudo systemctl status ragpp-mcp-server
curl -s http://127.0.0.1:8000/health || echo "Backend not responding"

# Expected: Service active, health endpoint returns 200
```

#### 4.2 Test Backend Endpoints
```bash
# Test basic endpoints
curl -s http://127.0.0.1:8000/test
curl -s -X POST http://127.0.0.1:8000/search -H "Content-Type: application/json" -d '{"query":"test","max_results":1}'

# Expected: Valid responses from backend
```

### 5. **Cloudflare Edge Configuration Audit**

#### 5.1 SSL/TLS Settings
**Manual Steps in Cloudflare Dashboard:**
1. Navigate to SSL/TLS → Overview
2. Verify SSL/TLS encryption mode: **"Flexible"** or **"Full"** (NOT Full Strict for HTTP origin)
3. Check Universal SSL Status: **"Active Certificate"**
4. Verify Always Use HTTPS: **"On"**

#### 5.2 Cache Rules Audit
**Manual Steps in Cloudflare Dashboard:**
1. Navigate to Caching → Cache Rules
2. Verify rules for:
   - `www.agourakis.med.br/*` → Cache static assets (.css, .js, .png, etc.)
   - `mcp.agourakis.med.br/mcp*` → **Bypass Cache**
   - `mcp.agourakis.med.br/sse*` → **Bypass Cache**

#### 5.3 WAF/Rate Limiting
**Manual Steps in Cloudflare Dashboard:**
1. Navigate to Security → WAF
2. Verify custom rules:
   - Rate limit `/mcp*` endpoints: Max 100 req/min per IP
   - **NEVER** rate limit `/sse*` endpoints
   - Block common attack patterns

### 6. **Network Connectivity Audit**

#### 6.1 Test Internal Network Paths
```bash
# Test internal connectivity
curl -s -I http://127.0.0.1:8440/ || echo "WWW port not accessible"
curl -s -I http://127.0.0.1:8480/ || echo "MCP port not accessible"

# Expected: Connection successful (after nginx config)
```

#### 6.2 Verify No External Port Exposure
```bash
# Ensure no external ports are exposed
sudo netstat -tulpn | grep -E ":8440|:8480|:8000" | grep -v "127.0.0.1"
sudo ufw status | grep -E "8440|8480|8000"

# Expected: No external bindings, no firewall rules for these ports
```

---

## 🔧 **FIX IMPLEMENTATION PLAN**

### Phase 1: Backup Current Configuration
```bash
# Create backup directory
sudo mkdir -p /opt/backups/$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/opt/backups/$(date +%Y%m%d-%H%M%S)"

# Backup existing configs
sudo cp /etc/cloudflared/config.yml ${BACKUP_DIR}/cloudflared-config.yml.backup
sudo cp -r /etc/nginx/sites-available ${BACKUP_DIR}/nginx-sites-available.backup
sudo cp -r /etc/nginx/sites-enabled ${BACKUP_DIR}/nginx-sites-enabled.backup
```

### Phase 2: Deploy New Configuration Files
```bash
# Deploy new cloudflared config
sudo cp /home/agourakis82/workspace/pcs-meta-repo/ops/config.yml /etc/cloudflared/config.yml
sudo chown root:root /etc/cloudflared/config.yml
sudo chmod 600 /etc/cloudflared/config.yml

# Deploy new nginx configurations
sudo cp /home/agourakis82/workspace/pcs-meta-repo/ops/nginx/www.internal.conf /etc/nginx/sites-available/
sudo cp /home/agourakis82/workspace/pcs-meta-repo/ops/nginx/mcp.internal.conf /etc/nginx/sites-available/

# Enable new sites
sudo ln -sf /etc/nginx/sites-available/www.internal.conf /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/mcp.internal.conf /etc/nginx/sites-enabled/

# Disable default site
sudo rm -f /etc/nginx/sites-enabled/default
```

### Phase 3: Service Restart & Validation
```bash
# Test nginx configuration
sudo nginx -t

# Restart services in correct order
sudo systemctl restart nginx
sudo systemctl restart cloudflared

# Wait for services to stabilize
sleep 10

# Verify services are running
sudo systemctl is-active nginx
sudo systemctl is-active cloudflared
sudo systemctl is-active ragpp-mcp-server
```

### Phase 4: Smoke Tests
```bash
# Run comprehensive smoke tests
/home/agourakis82/workspace/pcs-meta-repo/ops/tests-smoke.sh

# Expected: All tests pass, endpoints respond correctly
```

---

## 🚨 **ROLLBACK PROCEDURES**

### Emergency Rollback
```bash
# Restore from backup
BACKUP_DIR="/opt/backups/YYYYMMDD-HHMMSS"  # Replace with actual backup dir

sudo cp ${BACKUP_DIR}/cloudflared-config.yml.backup /etc/cloudflared/config.yml
sudo cp -r ${BACKUP_DIR}/nginx-sites-available.backup/* /etc/nginx/sites-available/
sudo cp -r ${BACKUP_DIR}/nginx-sites-enabled.backup/* /etc/nginx/sites-enabled/

# Restart services
sudo systemctl restart nginx
sudo systemctl restart cloudflared
```

### Disable Cloudflare Tunnel (Emergency)
```bash
# Stop cloudflared service
sudo systemctl stop cloudflared
sudo systemctl disable cloudflared

# Change DNS to grey cloud (manual in Cloudflare dashboard)
# Point DNS directly to server IP
```

---

## 📊 **MONITORING & OBSERVABILITY**

### Key Metrics to Monitor
- **Cloudflare Tunnel**: Connection status, latency, error rate
- **Nginx**: Request rate, response time, error rate
- **FastAPI**: Response time, queue depth, error rate
- **SSE Connections**: Active connections, reconnect rate, message latency

### SLOs (Service Level Objectives)
- **Website Response Time**: p95 < 500ms
- **API Response Time**: p95 < 1000ms
- **SSE Connection Success Rate**: > 99.5%
- **SSE Reconnect Time**: < 5 seconds

### Log Locations
- **Cloudflared**: `/var/log/cloudflared.log`
- **Nginx Access**: `/var/log/nginx/www-access.log`, `/var/log/nginx/mcp-access.log`
- **Nginx Error**: `/var/log/nginx/www-error.log`, `/var/log/nginx/mcp-error.log`
- **FastAPI**: `journalctl -u ragpp-mcp-server -f`

---

## ✅ **POST-DEPLOYMENT VERIFICATION**

### Final Checklist
- [ ] `https://www.agourakis.med.br` returns 200 OK
- [ ] `https://agourakis.med.br` redirects to `https://www.agourakis.med.br`
- [ ] `https://mcp.agourakis.med.br/health` returns 200 OK
- [ ] SSE endpoint `/sse` maintains long connections
- [ ] CORS headers present for `/mcp` endpoints
- [ ] No external ports exposed on server
- [ ] Cloudflare cache rules bypassing `/mcp` and `/sse`
- [ ] WAF rules protecting `/mcp` without blocking `/sse`
- [ ] All logs showing normal operation
- [ ] Monitoring dashboards showing healthy metrics

### Success Criteria
🎯 **Architecture successfully implements:**
- Zero inbound WAN ports (Cloudflare Tunnel only)
- TLS termination at Cloudflare edge
- Internal HTTP routing via nginx
- Robust SSE support with proper buffering controls
- Production-grade monitoring and logging
- Documented rollback procedures

---

**Status**: Ready for implementation  
**Next**: Execute Phase 1 (Backup) → Phase 2 (Deploy) → Phase 3 (Restart) → Phase 4 (Test)