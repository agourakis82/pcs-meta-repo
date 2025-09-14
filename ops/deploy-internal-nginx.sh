#!/bin/bash
# Nginx Internal Deployment Script
# Deploys internal-only nginx vhosts for production architecture
# Usage: ./deploy-internal-nginx.sh [--dry-run] [--rollback]

set -euo pipefail

# === CONFIGURATION VARIABLES ===
ORG_DOMAIN="agourakis.med.br"
WWW_HOST="www.agourakis.med.br"
MCP_HOST="mcp.agourakis.med.br"
WWW_PORT=8440
MCP_PORT=8480
NGINX_USER="www-data"

# File paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
BACKUP_DIR="/opt/backups/nginx-$(date +%Y%m%d-%H%M%S)"
WEBROOT="/var/www/pcs-meta-repo"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check if running with sufficient privileges
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Validate nginx is installed
check_nginx_installed() {
    log "Checking if nginx is installed..."
    
    if ! command -v nginx &> /dev/null; then
        error "nginx is not installed"
        exit 1
    fi
    
    local version=$(nginx -v 2>&1 | cut -d' ' -f3)
    success "nginx is installed: $version"
}

# Check if ports are available
check_ports_available() {
    log "Checking if target ports are available..."
    
    local ports=($WWW_PORT $MCP_PORT)
    
    for port in "${ports[@]}"; do
        if netstat -tulpn 2>/dev/null | grep ":$port " | grep -v "127.0.0.1:$port"; then
            error "Port $port is already in use by another service"
            netstat -tulpn | grep ":$port "
            return 1
        else
            success "Port $port is available"
        fi
    done
}

# Create backup of current configuration
create_backup() {
    log "Creating backup of current nginx configuration..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup existing sites-available and sites-enabled
    cp -r "$NGINX_SITES_AVAILABLE" "$BACKUP_DIR/"
    cp -r "$NGINX_SITES_ENABLED" "$BACKUP_DIR/"
    
    # Backup main nginx.conf
    cp /etc/nginx/nginx.conf "$BACKUP_DIR/"
    
    success "Backup created at: $BACKUP_DIR"
}

# Validate source configuration files
validate_source_configs() {
    log "Validating source configuration files..."
    
    local www_conf="$SCRIPT_DIR/nginx/www.internal.conf"
    local mcp_conf="$SCRIPT_DIR/nginx/mcp.internal.conf"
    
    if [[ ! -f "$www_conf" ]]; then
        error "WWW configuration file not found: $www_conf"
        exit 1
    fi
    
    if [[ ! -f "$mcp_conf" ]]; then
        error "MCP configuration file not found: $mcp_conf"
        exit 1
    fi
    
    success "Source configuration files validated"
}

# Create necessary directories and files
create_directories() {
    log "Creating necessary directories..."
    
    # Create webroot directory
    mkdir -p "$WEBROOT"
    chown -R "$NGINX_USER:$NGINX_USER" "$WEBROOT"
    
    # Create log directories
    mkdir -p /var/log/nginx
    
    # Create basic index.html if it doesn't exist
    if [[ ! -f "$WEBROOT/index.html" ]]; then
        log "Creating basic index.html..."
        cat > "$WEBROOT/index.html" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PCS Meta Repo</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { color: #333; }
        .status { color: #007bff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PCS Meta Repo</h1>
        <p class="status">Website is running successfully!</p>
        <p>API endpoint available at: <a href="https://mcp.agourakis.med.br">mcp.agourakis.med.br</a></p>
    </div>
</body>
</html>
EOF
        chown "$NGINX_USER:$NGINX_USER" "$WEBROOT/index.html"
        success "Basic index.html created"
    fi
}

# Deploy configuration files
deploy_configs() {
    log "Deploying nginx configuration files..."
    
    # Copy configuration files
    cp "$SCRIPT_DIR/nginx/www.internal.conf" "$NGINX_SITES_AVAILABLE/www.internal.conf"
    cp "$SCRIPT_DIR/nginx/mcp.internal.conf" "$NGINX_SITES_AVAILABLE/mcp.internal.conf"
    
    # Set correct permissions
    chmod 644 "$NGINX_SITES_AVAILABLE/www.internal.conf"
    chmod 644 "$NGINX_SITES_AVAILABLE/mcp.internal.conf"
    chown root:root "$NGINX_SITES_AVAILABLE/www.internal.conf"
    chown root:root "$NGINX_SITES_AVAILABLE/mcp.internal.conf"
    
    success "Configuration files deployed"
}

# Enable new sites
enable_sites() {
    log "Enabling new sites..."
    
    # Remove old symbolic links
    rm -f "$NGINX_SITES_ENABLED/default"
    rm -f "$NGINX_SITES_ENABLED/www.internal.conf"
    rm -f "$NGINX_SITES_ENABLED/mcp.internal.conf"
    
    # Create new symbolic links
    ln -sf "$NGINX_SITES_AVAILABLE/www.internal.conf" "$NGINX_SITES_ENABLED/"
    ln -sf "$NGINX_SITES_AVAILABLE/mcp.internal.conf" "$NGINX_SITES_ENABLED/"
    
    success "Sites enabled"
}

# Test nginx configuration
test_nginx_config() {
    log "Testing nginx configuration..."
    
    if nginx -t; then
        success "Nginx configuration test passed"
    else
        error "Nginx configuration test failed"
        return 1
    fi
}

# Reload nginx service
reload_nginx() {
    log "Reloading nginx service..."
    
    if systemctl reload nginx; then
        success "Nginx reloaded successfully"
    else
        error "Failed to reload nginx"
        return 1
    fi
}

# Verify nginx is running
verify_nginx_running() {
    log "Verifying nginx is running..."
    
    if systemctl is-active --quiet nginx; then
        success "Nginx service is active"
    else
        error "Nginx service is not active"
        systemctl status nginx --no-pager -l
        return 1
    fi
}

# Test internal endpoints
test_internal_endpoints() {
    log "Testing internal endpoints..."
    
    # Wait a moment for nginx to fully start
    sleep 3
    
    local endpoints=(
        "127.0.0.1:$WWW_PORT|WWW Site"
        "127.0.0.1:$MCP_PORT|MCP API"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local addr=$(echo "$endpoint" | cut -d'|' -f1)
        local name=$(echo "$endpoint" | cut -d'|' -f2)
        
        log "Testing $name at: $addr"
        
        if timeout 10 curl -s -I "http://$addr/" >/dev/null 2>&1; then
            success "$name is responding"
        else
            warning "$name is not responding (this may be expected if backend is not running)"
        fi
    done
}

# Show deployment summary
show_summary() {
    log "=== DEPLOYMENT SUMMARY ==="
    echo ""
    echo "Configuration files deployed:"
    echo "  - $NGINX_SITES_AVAILABLE/www.internal.conf (www.agourakis.med.br:$WWW_PORT)"
    echo "  - $NGINX_SITES_AVAILABLE/mcp.internal.conf (mcp.agourakis.med.br:$MCP_PORT)"
    echo ""
    echo "Enabled sites:"
    ls -la "$NGINX_SITES_ENABLED" | grep internal || echo "  No internal sites found"
    echo ""
    echo "Nginx status:"
    systemctl status nginx --no-pager -l | head -5
    echo ""
    echo "Listening ports:"
    netstat -tulpn | grep nginx | grep -E ":$WWW_PORT|:$MCP_PORT" || echo "  No nginx processes found on target ports"
    echo ""
    echo "Next steps:"
    echo "  1. Configure Cloudflare Tunnel to point to these internal ports"
    echo "  2. Start/configure FastAPI backend on port 8000"
    echo "  3. Test external connectivity via Cloudflare"
    echo ""
    success "Deployment completed successfully!"
}

# Rollback function
rollback() {
    log "Rolling back to previous configuration..."
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        error "No backup directory specified for rollback"
        echo "Usage: $0 --rollback /path/to/backup/directory"
        exit 1
    fi
    
    # Restore from backup
    cp -r "$BACKUP_DIR/sites-available/"* "$NGINX_SITES_AVAILABLE/"
    cp -r "$BACKUP_DIR/sites-enabled/"* "$NGINX_SITES_ENABLED/"
    
    # Test and reload
    if nginx -t; then
        systemctl reload nginx
        success "Rollback completed successfully"
    else
        error "Rollback failed - configuration test failed"
        return 1
    fi
}

# Dry run function
dry_run() {
    log "=== DRY RUN MODE ==="
    echo ""
    log "Would perform the following actions:"
    echo "  1. Create backup at: $BACKUP_DIR"
    echo "  2. Deploy configurations:"
    echo "     - www.internal.conf -> $NGINX_SITES_AVAILABLE/"
    echo "     - mcp.internal.conf -> $NGINX_SITES_AVAILABLE/"
    echo "  3. Enable sites in: $NGINX_SITES_ENABLED/"
    echo "  4. Test nginx configuration"
    echo "  5. Reload nginx service"
    echo "  6. Test internal endpoints"
    echo ""
    
    # Show what would be deployed
    log "Configuration files to deploy:"
    if [[ -f "$SCRIPT_DIR/nginx/www.internal.conf" ]]; then
        echo "  ✓ WWW config exists"
    else
        echo "  ✗ WWW config missing"
    fi
    
    if [[ -f "$SCRIPT_DIR/nginx/mcp.internal.conf" ]]; then
        echo "  ✓ MCP config exists"
    else
        echo "  ✗ MCP config missing"
    fi
    
    echo ""
    warning "This was a dry run - no changes were made"
}

# Main execution function
main() {
    echo "=============================================="
    echo "    NGINX INTERNAL DEPLOYMENT SCRIPT"
    echo "=============================================="
    echo ""
    
    # Parse command line arguments
    case "${1:-}" in
        --dry-run)
            dry_run
            exit 0
            ;;
        --rollback)
            BACKUP_DIR="${2:-}"
            rollback
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [--dry-run] [--rollback /path/to/backup]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Show what would be done without making changes"
            echo "  --rollback   Restore from backup directory"
            echo "  --help       Show this help message"
            exit 0
            ;;
    esac
    
    # Perform checks
    check_permissions
    check_nginx_installed
    check_ports_available
    validate_source_configs
    
    # Create backup
    create_backup
    
    # Deploy configuration
    create_directories
    deploy_configs
    enable_sites
    
    # Test and reload
    if test_nginx_config; then
        reload_nginx
        verify_nginx_running
        test_internal_endpoints
        show_summary
    else
        error "Configuration test failed - rolling back..."
        rollback
        exit 1
    fi
}

# Error handling
trap 'error "Script interrupted"; exit 1' INT TERM

# Execute main function
main "$@"