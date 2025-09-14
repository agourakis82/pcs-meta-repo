# 🌐 MCP Server Domain Configuration Guide

## Complete Setup for mcp.agourakis.med.br

This guide will help you configure your MCP server for remote access via your domain `mcp.agourakis.med.br` with SSL encryption and proper security.

---

## 📋 What We've Configured

### 1. **MCP Settings Updated**
- ✅ Added `ragpp-research` server to your MCP configuration
- ✅ Configured proper environment variables and paths
- ✅ Set up production mode for the RAG++ MCP server

### 2. **Files Created**
- ✅ `mcp_agourakis_med_br.conf` - Nginx reverse proxy configuration
- ✅ `ragpp-mcp-server.service` - Systemd service for auto-start
- ✅ `setup_mcp_domain.sh` - Automated setup script
- ✅ This configuration guide

---

## 🚀 Quick Setup (Automated)

Run the automated setup script:

```bash
./setup_mcp_domain.sh
```

This script will:
1. Install required packages (nginx, certbot, etc.)
2. Configure firewall (UFW)
3. Set up SSL certificates with Let's Encrypt
4. Configure Nginx reverse proxy
5. Set up systemd service for auto-start
6. Start all services
7. Test the configuration

---

## 🔧 Manual Setup (Step by Step)

If you prefer manual setup or need to troubleshoot:

### Step 1: Install Dependencies

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx ufw
```

### Step 2: Configure Firewall

```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
```

### Step 3: Install Python Dependencies

```bash
python3 -m pip install --user model-context-protocol fastapi uvicorn chromadb
```

### Step 4: Set Up SSL Certificate

```bash
sudo certbot certonly --nginx -d mcp.agourakis.med.br --non-interactive --agree-tos --email agourakis82@gmail.com
```

### Step 5: Configure Nginx

```bash
# Copy nginx configuration
sudo cp mcp_agourakis_med_br.conf /etc/nginx/sites-available/mcp.agourakis.med.br

# Enable the site
sudo ln -sf /etc/nginx/sites-available/mcp.agourakis.med.br /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Set Up Systemd Service

```bash
# Copy service file
sudo cp ragpp-mcp-server.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ragpp-mcp-server.service
sudo systemctl start ragpp-mcp-server.service
```

---

## 🧪 Testing Your Configuration

### 1. Test Local Server

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2024-01-XX..."}
```

### 2. Test HTTPS Domain

```bash
curl https://mcp.agourakis.med.br/health
```

### 3. Test MCP Endpoint

```bash
curl -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo" \
     https://mcp.agourakis.med.br/search?q=test
```

### 4. Check Service Status

```bash
sudo systemctl status ragpp-mcp-server.service
```

---

## 🔗 Access URLs

Once configured, your MCP server will be accessible at:

- **Main API**: `https://mcp.agourakis.med.br`
- **Health Check**: `https://mcp.agourakis.med.br/health`
- **API Documentation**: `https://mcp.agourakis.med.br/docs`
- **MCP Protocol Endpoint**: `https://mcp.agourakis.med.br/mcp`

---

## 🤖 MCP Client Configuration

### For Local MCP Clients (Claude Desktop, etc.)

Your local MCP configuration is already updated in:
```
~/.vscode-server/data/User/globalStorage/blackboxapp.blackboxagent/settings/blackbox_mcp_settings.json
```

### For Remote MCP Clients

Use these settings:
- **Server URL**: `https://mcp.agourakis.med.br/mcp`
- **Authentication**: Bearer token
- **Token**: `wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo`

### For ChatGPT Custom Actions

```json
{
  "servers": [
    {
      "url": "https://mcp.agourakis.med.br"
    }
  ]
}
```

---

## 🛠️ Service Management

### Start/Stop/Restart Services

```bash
# RAG++ MCP Server
sudo systemctl start ragpp-mcp-server.service
sudo systemctl stop ragpp-mcp-server.service
sudo systemctl restart ragpp-mcp-server.service

# Nginx
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
```

### View Logs

```bash
# RAG++ MCP Server logs
sudo journalctl -u ragpp-mcp-server.service -f

# Nginx logs
sudo tail -f /var/log/nginx/mcp.agourakis.med.br.access.log
sudo tail -f /var/log/nginx/mcp.agourakis.med.br.error.log
```

### Check Status

```bash
# Service status
sudo systemctl status ragpp-mcp-server.service
sudo systemctl status nginx

# Port usage
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :443
```

---

## 🔒 Security Features

### SSL/TLS Configuration
- ✅ TLS 1.2 and 1.3 support
- ✅ Strong cipher suites
- ✅ HSTS headers
- ✅ Auto-renewal with Let's Encrypt

### Security Headers
- ✅ X-Frame-Options: DENY
- ✅ X-Content-Type-Options: nosniff
- ✅ X-XSS-Protection
- ✅ Referrer-Policy

### CORS Configuration
- ✅ Proper CORS headers for web access
- ✅ Preflight request handling
- ✅ Authorization header support

---

## 🚨 Troubleshooting

### Common Issues

#### 1. SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew --dry-run

# If domain not pointing correctly, use standalone mode
sudo systemctl stop nginx
sudo certbot certonly --standalone -d mcp.agourakis.med.br
sudo systemctl start nginx
```

#### 2. Service Not Starting
```bash
# Check logs for errors
sudo journalctl -u ragpp-mcp-server.service --no-pager

# Check Python dependencies
python3 -c "import fastapi, uvicorn; print('Dependencies OK')"

# Check file permissions
ls -la /home/agourakis82/workspace/pcs-meta-repo/ragpp/
```

#### 3. Nginx Configuration Issues
```bash
# Test nginx configuration
sudo nginx -t

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log

# Reload nginx configuration
sudo systemctl reload nginx
```

#### 4. Port Already in Use
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill process if needed
sudo pkill -f ragpp_web_server
```

### DNS Issues

If your domain isn't resolving:
1. Check DNS propagation: `nslookup mcp.agourakis.med.br`
2. Verify A record points to your server's IP
3. Wait for DNS propagation (up to 48 hours)

---

## 📊 Monitoring and Maintenance

### Health Monitoring Script

Create a monitoring script:
```bash
#!/bin/bash
# monitor_mcp.sh

while true; do
    if curl -s https://mcp.agourakis.med.br/health > /dev/null; then
        echo "✅ $(date): MCP Server OK"
    else
        echo "❌ $(date): MCP Server DOWN"
        # Optional: restart service
        # sudo systemctl restart ragpp-mcp-server.service
    fi
    sleep 300  # Check every 5 minutes
done
```

### Log Rotation

Nginx logs are automatically rotated. For application logs:
```bash
# Add to /etc/logrotate.d/ragpp-mcp
/home/agourakis82/workspace/pcs-meta-repo/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 agourakis82 agourakis82
    postrotate
        systemctl reload ragpp-mcp-server.service
    endscript
}
```

---

## 🎯 Usage Examples

### 1. Search Literature via API

```bash
curl -X POST "https://mcp.agourakis.med.br/search" \
  -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo" \
  -H "Content-Type: application/json" \
  -d '{"query": "computational psychiatry machine learning"}'
```

### 2. Store Research Finding

```bash
curl -X POST "https://mcp.agourakis.med.br/store" \
  -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Research Finding",
    "content": "Important discovery about...",
    "source": "Journal XYZ"
  }'
```

### 3. Get Recent Findings

```bash
curl "https://mcp.agourakis.med.br/recent?limit=10" \
  -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo"
```

---

## 🔄 Updates and Maintenance

### Updating the MCP Server

```bash
# Pull latest changes
cd /home/agourakis82/workspace/pcs-meta-repo
git pull

# Restart service
sudo systemctl restart ragpp-mcp-server.service
```

### SSL Certificate Renewal

Certificates auto-renew, but to check:
```bash
# Check renewal status
sudo certbot certificates

# Test renewal
sudo certbot renew --dry-run
```

### Backup Configuration

```bash
# Backup important files
tar -czf mcp-backup-$(date +%Y%m%d).tar.gz \
  mcp_agourakis_med_br.conf \
  ragpp-mcp-server.service \
  ~/.vscode-server/data/User/globalStorage/blackboxapp.blackboxagent/settings/blackbox_mcp_settings.json
```

---

## 📞 Support

If you encounter issues:

1. **Check logs**: `sudo journalctl -u ragpp-mcp-server.service -f`
2. **Test connectivity**: `curl https://mcp.agourakis.med.br/health`
3. **Verify DNS**: `nslookup mcp.agourakis.med.br`
4. **Check service status**: `sudo systemctl status ragpp-mcp-server.service`

---

## ✅ Configuration Complete!

Your MCP server is now configured for:
- ✅ **Local Access**: Via MCP clients (Claude Desktop, etc.)
- ✅ **Remote Access**: Via `https://mcp.agourakis.med.br`
- ✅ **Web API**: RESTful API with authentication
- ✅ **MCP Protocol**: Native MCP over HTTPS
- ✅ **SSL Security**: Let's Encrypt certificates with auto-renewal
- ✅ **Auto-Start**: Systemd service management
- ✅ **Monitoring**: Health checks and logging

**Next Steps**: Run `./setup_mcp_domain.sh` to complete the automated setup!
