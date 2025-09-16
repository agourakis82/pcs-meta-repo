#!/bin/bash
# Cloudflare Tunnel Verification Script
# Idempotent script for checking tunnel status and logs
# Usage: ./cloudflared-verify.sh [--tail-logs]

set -euo pipefail

# === CONFIGURATION VARIABLES ===
CLOUDFLARED_TUNNEL_NAME="agourakis"
CLOUDFLARED_UUID="REPLACE_WITH_REAL_UUID"
CONFIG_FILE="/etc/cloudflared/config.yml"
LOG_FILE="/var/log/cloudflared.log"
CREDS_FILE="/etc/cloudflared/${CLOUDFLARED_UUID}.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root for certain operations
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        warning "Running as root - be careful with file permissions"
    fi
}

# Verify cloudflared is installed
check_cloudflared_installed() {
    log "Checking if cloudflared is installed..."
    
    if ! command -v cloudflared &> /dev/null; then
        error "cloudflared is not installed or not in PATH"
        exit 1
    fi
    
    local version=$(cloudflared version 2>/dev/null | head -1)
    success "cloudflared is installed: $version"
}

# Check systemd service status
check_service_status() {
    log "Checking cloudflared service status..."
    
    if systemctl is-active --quiet cloudflared; then
        success "cloudflared service is active"
        systemctl status cloudflared --no-pager -l | head -10
    else
        error "cloudflared service is not active"
        systemctl status cloudflared --no-pager -l || true
        return 1
    fi
}

# List all tunnels
list_tunnels() {
    log "Listing all Cloudflare tunnels..."
    
    if cloudflared tunnel list 2>/dev/null; then
        success "Tunnel list retrieved successfully"
    else
        error "Failed to list tunnels - check credentials and connectivity"
        return 1
    fi
}

# Get specific tunnel info
get_tunnel_info() {
    log "Getting tunnel information for: $CLOUDFLARED_TUNNEL_NAME"
    
    if cloudflared tunnel info "$CLOUDFLARED_TUNNEL_NAME" 2>/dev/null; then
        success "Tunnel information retrieved"
    else
        error "Failed to get tunnel info for: $CLOUDFLARED_TUNNEL_NAME"
        return 1
    fi
}

# Verify configuration files
check_config_files() {
    log "Checking configuration files..."
    
    # Check main config file
    if [[ -f "$CONFIG_FILE" ]]; then
        success "Configuration file exists: $CONFIG_FILE"
        local config_perms=$(stat -c "%a" "$CONFIG_FILE")
        log "Configuration file permissions: $config_perms"
        
        # Validate YAML syntax
        if python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>/dev/null; then
            success "Configuration file has valid YAML syntax"
        else
            error "Configuration file has invalid YAML syntax"
            return 1
        fi
    else
        error "Configuration file not found: $CONFIG_FILE"
        return 1
    fi
    
    # Check credentials file
    if [[ -f "$CREDS_FILE" ]]; then
        success "Credentials file exists: $CREDS_FILE"
        local creds_perms=$(stat -c "%a" "$CREDS_FILE")
        log "Credentials file permissions: $creds_perms"
        
        if [[ "$creds_perms" != "600" ]]; then
            warning "Credentials file permissions should be 600"
        fi
    else
        error "Credentials file not found: $CREDS_FILE"
        warning "Update CLOUDFLARED_UUID variable with correct tunnel ID"
        return 1
    fi
}

# Display current ingress configuration
show_ingress_config() {
    log "Current ingress configuration:"
    
    if [[ -f "$CONFIG_FILE" ]]; then
        echo "----------------------------------------"
        grep -A 20 "ingress:" "$CONFIG_FILE" || true
        echo "----------------------------------------"
    else
        error "Cannot read configuration file"
        return 1
    fi
}

# Test tunnel connectivity
test_tunnel_connectivity() {
    log "Testing tunnel connectivity..."
    
    # Try dry run
    if timeout 30 cloudflared tunnel run --dry-run "$CLOUDFLARED_TUNNEL_NAME" 2>/dev/null; then
        success "Tunnel dry run successful"
    else
        error "Tunnel dry run failed"
        return 1
    fi
}

# Check DNS resolution
check_dns_resolution() {
    log "Checking DNS resolution for configured hostnames..."
    
    local hostnames=("www.agourakis.med.br" "mcp.agourakis.med.br" "agourakis.med.br")
    
    for hostname in "${hostnames[@]}"; do
        log "Checking DNS for: $hostname"
        
        if dig +short "$hostname" | grep -q .; then
            local ips=$(dig +short "$hostname" | tr '\n' ' ')
            success "$hostname resolves to: $ips"
        else
            error "$hostname does not resolve"
        fi
    done
}

# Show recent logs
show_recent_logs() {
    log "Recent cloudflared logs (last 20 lines):"
    
    if [[ -f "$LOG_FILE" ]]; then
        echo "----------------------------------------"
        tail -20 "$LOG_FILE" || true
        echo "----------------------------------------"
    else
        warning "Log file not found: $LOG_FILE"
        log "Checking systemd logs instead:"
        journalctl -u cloudflared --no-pager -n 20 || true
    fi
}

# Tail logs in real-time
tail_logs() {
    log "Tailing cloudflared logs (Ctrl+C to stop)..."
    
    if [[ -f "$LOG_FILE" ]]; then
        tail -f "$LOG_FILE"
    else
        warning "Log file not found, tailing systemd logs:"
        journalctl -u cloudflared -f
    fi
}

# Test internal endpoints
test_internal_endpoints() {
    log "Testing internal nginx endpoints..."
    
    local endpoints=(
        "127.0.0.1:8440|WWW"
        "127.0.0.1:8480|MCP"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local addr=$(echo "$endpoint" | cut -d'|' -f1)
        local name=$(echo "$endpoint" | cut -d'|' -f2)
        
        log "Testing $name endpoint: $addr"
        
        if timeout 5 curl -s -I "http://$addr/" >/dev/null 2>&1; then
            success "$name endpoint is responding"
        else
            error "$name endpoint is not responding"
        fi
    done
}

# Generate tunnel metrics
show_tunnel_metrics() {
    log "Tunnel metrics (if available):"
    
    # Try to get metrics from cloudflared
    if curl -s "http://127.0.0.1:60123/metrics" 2>/dev/null | head -10; then
        success "Metrics endpoint is accessible"
    else
        warning "Metrics endpoint not accessible (127.0.0.1:60123)"
    fi
}

# Main execution
main() {
    echo "=============================================="
    echo "    CLOUDFLARE TUNNEL VERIFICATION SCRIPT"
    echo "=============================================="
    echo ""
    
    check_permissions
    
    # Core checks
    check_cloudflared_installed
    check_service_status
    check_config_files
    
    echo ""
    log "=== TUNNEL STATUS ==="
    list_tunnels
    echo ""
    get_tunnel_info
    
    echo ""
    log "=== CONFIGURATION ==="
    show_ingress_config
    
    echo ""
    log "=== CONNECTIVITY TESTS ==="
    check_dns_resolution
    test_tunnel_connectivity
    test_internal_endpoints
    
    echo ""
    log "=== METRICS ==="
    show_tunnel_metrics
    
    echo ""
    log "=== RECENT LOGS ==="
    show_recent_logs
    
    echo ""
    success "Verification complete!"
    
    # Handle tail logs option
    if [[ "${1:-}" == "--tail-logs" ]]; then
        echo ""
        tail_logs
    else
        echo ""
        log "Run with --tail-logs to monitor logs in real-time"
    fi
}

# Error handling
trap 'error "Script interrupted"; exit 1' INT TERM

# Execute main function
main "$@"