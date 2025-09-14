#!/bin/bash

# DEPRECATED: Tailscale Funnel Fix Script
# ==========================================
# ⚠️  ESTE ARQUIVO FOI DEPRECIADO ⚠️
# 
# MIGRADO PARA: Cloudflare Tunnel (cloudflared)
# NOVO GUIA: docs/infra_cloudflare_tunnel.md
# 
# Razões da migração:
# - Melhor performance global
# - Domínio personalizado sem limitações
# - DDoS protection incluído
# - TLS automático via Cloudflare
# - Configuração mais simples
#
# Este arquivo permanece apenas para compatibilidade histórica.
# ==========================================

# Tailscale Funnel Fix Script (DEPRECATED)
# Fixes common Tailscale serve/funnel configuration issues
# Supports custom domain: agourakis.med.br

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MCP_PORT="8000"
HTTPS_PORT="443"
HTTP_PORT="80"
CUSTOM_DOMAIN="agourakis.med.br"
MCP_SERVICE_NAME="ragpp-mcp-server"

echo -e "${BLUE}🔧 Tailscale Funnel Fix Script${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "Custom Domain: ${GREEN}$CUSTOM_DOMAIN${NC}"
echo -e "MCP Port: ${GREEN}$MCP_PORT${NC}"
echo ""

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    elif [ "$status" = "ERROR" ]; then
        echo -e "${RED}❌ $message${NC}"
    else
        echo -e "${BLUE}ℹ️  $message${NC}"
    fi
}

# Function to run command with error handling
run_command() {
    local cmd="$1"
    local description="$2"
    
    echo -e "${BLUE}Running: ${NC}$cmd"
    if eval "$cmd"; then
        print_status "OK" "$description completed successfully"
        return 0
    else
        print_status "ERROR" "$description failed"
        return 1
    fi
}

# 1. Check Tailscale installation and status
echo -e "${BLUE}📋 Step 1: Checking Tailscale Status${NC}"
echo "----------------------------------------"

if ! command -v tailscale &> /dev/null; then
    print_status "ERROR" "Tailscale is not installed"
    echo "Please install Tailscale first: https://tailscale.com/download"
    exit 1
fi

print_status "OK" "Tailscale CLI found"

# Check if Tailscale is running and connected
if ! tailscale status &> /dev/null; then
    print_status "ERROR" "Tailscale is not running or not logged in"
    echo ""
    echo -e "${YELLOW}To fix this:${NC}"
    echo "1. Start Tailscale: sudo systemctl start tailscaled"
    echo "2. Login: tailscale up"
    exit 1
fi

print_status "OK" "Tailscale is running and connected"

# Get Tailscale info
TAILSCALE_IP=$(tailscale status --json | jq -r '.Self.TailscaleIPs[0]' 2>/dev/null || echo "unknown")
TAILSCALE_DOMAIN=$(tailscale status --json | jq -r '.Self.DNSName' 2>/dev/null || echo "unknown")

echo -e "Tailscale IP: ${GREEN}$TAILSCALE_IP${NC}"
echo -e "Tailscale Domain: ${GREEN}$TAILSCALE_DOMAIN${NC}"
echo ""

# 2. Check MCP Server Status
echo -e "${BLUE}📋 Step 2: Checking MCP Server${NC}"
echo "-------------------------------"

# Check if MCP service is running
if systemctl is-active --quiet $MCP_SERVICE_NAME 2>/dev/null; then
    print_status "OK" "MCP service ($MCP_SERVICE_NAME) is running"
else
    print_status "WARN" "MCP service ($MCP_SERVICE_NAME) is not running"
    echo -e "${YELLOW}Attempting to start MCP service...${NC}"
    if sudo systemctl start $MCP_SERVICE_NAME; then
        print_status "OK" "MCP service started successfully"
        sleep 3
    else
        print_status "ERROR" "Failed to start MCP service"
        echo "Please check the service manually: sudo systemctl status $MCP_SERVICE_NAME"
    fi
fi

# Test local MCP server connectivity
echo -e "${BLUE}Testing local MCP server connectivity...${NC}"
if curl -s -f --connect-timeout 5 http://localhost:$MCP_PORT/health > /dev/null; then
    print_status "OK" "MCP server responding on localhost:$MCP_PORT"
else
    print_status "ERROR" "MCP server not responding on localhost:$MCP_PORT"
    echo ""
    echo -e "${YELLOW}Troubleshooting steps:${NC}"
    echo "1. Check if service is running: sudo systemctl status $MCP_SERVICE_NAME"
    echo "2. Check logs: sudo journalctl -u $MCP_SERVICE_NAME -f"
    echo "3. Check if port is in use: sudo netstat -tlnp | grep :$MCP_PORT"
    exit 1
fi
echo ""

# 3. Clear existing Tailscale serve/funnel configuration
echo -e "${BLUE}📋 Step 3: Clearing Existing Configuration${NC}"
echo "-------------------------------------------"

echo -e "${BLUE}Clearing any existing serve configuration...${NC}"
tailscale serve reset 2>/dev/null || true
print_status "OK" "Existing serve configuration cleared"

echo -e "${BLUE}Stopping any existing funnel...${NC}"
tailscale funnel --https=$HTTPS_PORT off 2>/dev/null || true
tailscale funnel --http=$HTTP_PORT off 2>/dev/null || true
print_status "OK" "Existing funnel configuration cleared"
echo ""

# 4. Configure Tailscale Serve
echo -e "${BLUE}📋 Step 4: Configuring Tailscale Serve${NC}"
echo "---------------------------------------"

echo -e "${BLUE}Setting up HTTPS serve on port $HTTPS_PORT...${NC}"
if run_command "tailscale serve --https=$HTTPS_PORT $MCP_PORT" "HTTPS serve configuration"; then
    print_status "OK" "HTTPS serve configured successfully"
else
    print_status "WARN" "HTTPS serve failed, trying HTTP..."
    if run_command "tailscale serve --http=$HTTP_PORT $MCP_PORT" "HTTP serve configuration"; then
        print_status "OK" "HTTP serve configured successfully"
        HTTPS_PORT=$HTTP_PORT
    else
        print_status "ERROR" "Both HTTPS and HTTP serve configuration failed"
        exit 1
    fi
fi
echo ""

# 5. Enable Tailscale Funnel
echo -e "${BLUE}📋 Step 5: Enabling Tailscale Funnel${NC}"
echo "-------------------------------------"

if [ "$HTTPS_PORT" = "443" ]; then
    echo -e "${BLUE}Enabling HTTPS funnel on port $HTTPS_PORT...${NC}"
    if run_command "tailscale funnel --https=$HTTPS_PORT on" "HTTPS funnel activation"; then
        FUNNEL_URL="https://$TAILSCALE_DOMAIN"
        print_status "OK" "HTTPS funnel enabled successfully"
    else
        print_status "ERROR" "HTTPS funnel activation failed"
        echo ""
        echo -e "${YELLOW}This might be because:${NC}"
        echo "1. Your Tailscale account doesn't have funnel enabled"
        echo "2. HTTPS funnel requires a paid Tailscale plan for some use cases"
        echo "3. There might be network restrictions"
        echo ""
        echo -e "${BLUE}Trying HTTP funnel instead...${NC}"
        tailscale serve reset
        run_command "tailscale serve --http=$HTTP_PORT $MCP_PORT" "HTTP serve configuration"
        if run_command "tailscale funnel --http=$HTTP_PORT on" "HTTP funnel activation"; then
            FUNNEL_URL="http://$TAILSCALE_DOMAIN"
            print_status "OK" "HTTP funnel enabled successfully"
        else
            print_status "ERROR" "Both HTTPS and HTTP funnel activation failed"
            exit 1
        fi
    fi
else
    echo -e "${BLUE}Enabling HTTP funnel on port $HTTP_PORT...${NC}"
    if run_command "tailscale funnel --http=$HTTP_PORT on" "HTTP funnel activation"; then
        FUNNEL_URL="http://$TAILSCALE_DOMAIN"
        print_status "OK" "HTTP funnel enabled successfully"
    else
        print_status "ERROR" "HTTP funnel activation failed"
        exit 1
    fi
fi
echo ""

# 6. Configure Custom Domain (if different from Tailscale domain)
echo -e "${BLUE}📋 Step 6: Custom Domain Configuration${NC}"
echo "--------------------------------------"

if [ "$CUSTOM_DOMAIN" != "$TAILSCALE_DOMAIN" ]; then
    echo -e "${BLUE}Setting up custom domain: $CUSTOM_DOMAIN${NC}"
    echo ""
    echo -e "${YELLOW}DNS Configuration Required:${NC}"
    echo "You need to create a CNAME record in your DNS:"
    echo ""
    echo -e "Record Type: ${GREEN}CNAME${NC}"
    echo -e "Name: ${GREEN}$CUSTOM_DOMAIN${NC}"
    echo -e "Value: ${GREEN}$TAILSCALE_DOMAIN${NC}"
    echo ""
    echo -e "${BLUE}After setting up the CNAME, your MCP server will be available at:${NC}"
    if [ "$HTTPS_PORT" = "443" ]; then
        CUSTOM_URL="https://$CUSTOM_DOMAIN"
    else
        CUSTOM_URL="http://$CUSTOM_DOMAIN"
    fi
    echo -e "${GREEN}$CUSTOM_URL${NC}"
else
    CUSTOM_URL="$FUNNEL_URL"
fi
echo ""

# 7. Test the configuration
echo -e "${BLUE}📋 Step 7: Testing Configuration${NC}"
echo "---------------------------------"

echo -e "${BLUE}Testing Tailscale domain access...${NC}"
sleep 5  # Give some time for the configuration to propagate

if curl -s -f --connect-timeout 10 "$FUNNEL_URL/health" > /dev/null; then
    print_status "OK" "Tailscale funnel is working: $FUNNEL_URL"
else
    print_status "WARN" "Tailscale funnel test failed (this might be normal initially)"
    echo "URL: $FUNNEL_URL/health"
fi

if [ "$CUSTOM_DOMAIN" != "$TAILSCALE_DOMAIN" ]; then
    echo -e "${BLUE}Testing custom domain access (may fail if DNS not configured)...${NC}"
    if curl -s -f --connect-timeout 10 "$CUSTOM_URL/health" > /dev/null; then
        print_status "OK" "Custom domain is working: $CUSTOM_URL"
    else
        print_status "WARN" "Custom domain test failed (DNS may not be configured yet)"
        echo "URL: $CUSTOM_URL/health"
    fi
fi
echo ""

# 8. Display current configuration
echo -e "${BLUE}📋 Step 8: Current Configuration${NC}"
echo "---------------------------------"

echo -e "${BLUE}Tailscale serve status:${NC}"
tailscale serve status

echo ""
echo -e "${BLUE}Tailscale funnel status:${NC}"
tailscale funnel status
echo ""

# 9. Summary and next steps
echo -e "${BLUE}🎉 Configuration Complete!${NC}"
echo "=========================="
echo ""
echo -e "${GREEN}✅ MCP Server Status:${NC} Running on localhost:$MCP_PORT"
echo -e "${GREEN}✅ Tailscale Serve:${NC} Configured"
echo -e "${GREEN}✅ Tailscale Funnel:${NC} Enabled"
echo ""
echo -e "${BLUE}📡 Access URLs:${NC}"
echo -e "Tailscale Domain: ${GREEN}$FUNNEL_URL${NC}"
if [ "$CUSTOM_DOMAIN" != "$TAILSCALE_DOMAIN" ]; then
    echo -e "Custom Domain: ${GREEN}$CUSTOM_URL${NC} ${YELLOW}(requires DNS setup)${NC}"
fi
echo ""
echo -e "${BLUE}🧪 Test Endpoints:${NC}"
echo -e "Health Check: ${GREEN}$FUNNEL_URL/health${NC}"
echo -e "API Docs: ${GREEN}$FUNNEL_URL/docs${NC}"
echo -e "Memory Search: ${GREEN}$FUNNEL_URL/memory/search${NC}"
echo ""

if [ "$CUSTOM_DOMAIN" != "$TAILSCALE_DOMAIN" ]; then
    echo -e "${YELLOW}📝 DNS Setup Required:${NC}"
    echo "To use your custom domain ($CUSTOM_DOMAIN), create this DNS record:"
    echo ""
    echo -e "Type: ${GREEN}CNAME${NC}"
    echo -e "Name: ${GREEN}$CUSTOM_DOMAIN${NC}"
    echo -e "Value: ${GREEN}$TAILSCALE_DOMAIN${NC}"
    echo ""
fi

echo -e "${BLUE}🔧 Management Commands:${NC}"
echo "To stop funnel: tailscale funnel --https=$HTTPS_PORT off"
echo "To reset serve: tailscale serve reset"
echo "To check status: tailscale serve status && tailscale funnel status"
echo ""

# Create a quick test script
cat > test_mcp_funnel.sh << EOF
#!/bin/bash
# Quick test script for MCP funnel

echo "🧪 Testing MCP Funnel Endpoints..."
echo ""

# Test Tailscale domain
echo "Testing Tailscale domain: $FUNNEL_URL"
curl -s "$FUNNEL_URL/health" | jq . || echo "❌ Failed"
echo ""

# Test custom domain if different
if [ "$CUSTOM_DOMAIN" != "$TAILSCALE_DOMAIN" ]; then
    echo "Testing custom domain: $CUSTOM_URL"
    curl -s "$CUSTOM_URL/health" | jq . || echo "❌ Failed or DNS not configured"
    echo ""
fi

echo "✅ Test complete"
EOF

chmod +x test_mcp_funnel.sh
print_status "OK" "Created test_mcp_funnel.sh for quick testing"

echo -e "${GREEN}🎯 Setup complete! Your MCP server is now accessible via Tailscale funnel.${NC}"
