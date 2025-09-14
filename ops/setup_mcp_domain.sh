ecessário#!/bin/bash

# MCP Server Domain Setup Script
# Configures mcp.agourakis.med.br with SSL and reverse proxy

set -e  # Exit on any error

echo "🌐 Setting up MCP Server for mcp.agourakis.med.br"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="mcp.agourakis.med.br"
PROJECT_DIR="/home/agourakis82/workspace/pcs-meta-repo"
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
SYSTEMD_DIR="/etc/systemd/system"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for system configuration
check_sudo() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root directly."
        print_status "Run with: ./setup_mcp_domain.sh"
        print_status "It will ask for sudo when needed."
        exit 1
    fi
}

# Install required packages
install_dependencies() {
    print_status "Installing required packages..."
    
    sudo apt update
    sudo apt install -y nginx certbot python3-certbot-nginx ufw
    
    print_success "Dependencies installed"
}

# Configure firewall
setup_firewall() {
    print_status "Configuring firewall..."
    
    # Enable UFW if not already enabled
    sudo ufw --force enable
    
    # Allow SSH, HTTP, HTTPS
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8000/tcp  # For direct access if needed
    
    print_success "Firewall configured"
}

# Install SSL certificate
setup_ssl() {
    print_status "Setting up SSL certificate for $DOMAIN..."
    
    # Check if certificate already exists
    if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
        print_warning "SSL certificate already exists for $DOMAIN"
        return 0
    fi
    
    # Get SSL certificate
    sudo certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos --email agourakis82@gmail.com
    
    if [[ $? -eq 0 ]]; then
        print_success "SSL certificate obtained for $DOMAIN"
        
        # Set up auto-renewal
        sudo systemctl enable certbot.timer
        sudo systemctl start certbot.timer
        print_success "SSL auto-renewal configured"
    else
        print_error "Failed to obtain SSL certificate"
        print_warning "You may need to:"
        print_warning "1. Ensure $DOMAIN points to this server's IP"
        print_warning "2. Temporarily stop nginx: sudo systemctl stop nginx"
        print_warning "3. Run: sudo certbot certonly --standalone -d $DOMAIN"
        exit 1
    fi
}

# Configure Nginx
setup_nginx() {
    print_status "Configuring Nginx for $DOMAIN..."
    
    # Copy our nginx configuration
    sudo cp "$PROJECT_DIR/mcp_agourakis_med_br.conf" "$NGINX_SITES_AVAILABLE/$DOMAIN"
    
    # Enable the site
    sudo ln -sf "$NGINX_SITES_AVAILABLE/$DOMAIN" "$NGINX_SITES_ENABLED/$DOMAIN"
    
    # Remove default site if it exists
    sudo rm -f "$NGINX_SITES_ENABLED/default"
    
    # Test nginx configuration
    sudo nginx -t
    
    if [[ $? -eq 0 ]]; then
        print_success "Nginx configuration is valid"
        sudo systemctl reload nginx
        print_success "Nginx reloaded"
    else
        print_error "Nginx configuration test failed"
        exit 1
    fi
}

# Setup systemd service
setup_systemd_service() {
    print_status "Setting up systemd service..."
    
    # Copy service file
    sudo cp "$PROJECT_DIR/ragpp-mcp-server.service" "$SYSTEMD_DIR/"
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable ragpp-mcp-server.service
    
    print_success "Systemd service configured"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    # Create data directory if it doesn't exist
    mkdir -p "$PROJECT_DIR/ragpp/data"
    mkdir -p "$PROJECT_DIR/logs"
    
    # Set proper permissions
    chmod 755 "$PROJECT_DIR/ragpp/data"
    chmod 755 "$PROJECT_DIR/logs"
    
    print_success "Directories created"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    cd "$PROJECT_DIR"
    
    # Install web server requirements
    if [[ -f "requirements-web.txt" ]]; then
        python3 -m pip install --user -r requirements-web.txt
        print_success "Web server dependencies installed from requirements-web.txt"
    else
        # Fallback to individual packages with correct names
        python3 -m pip install --user mcp>=1.0.0
        python3 -m pip install --user fastapi>=0.104.0 uvicorn[standard]>=0.24.0
        python3 -m pip install --user chromadb>=0.4.0 sentence-transformers>=2.2.0
        print_success "Web server dependencies installed individually"
    fi
    
    print_success "Python dependencies installed"
}

# Start services
start_services() {
    print_status "Starting services..."
    
    # Start and enable nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx
    
    # Start RAG++ MCP server
    sudo systemctl start ragpp-mcp-server.service
    
    print_success "Services started"
}

# Test configuration
test_setup() {
    print_status "Testing configuration..."
    
    # Test local connection
    sleep 5  # Give services time to start
    
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Local server is responding"
    else
        print_warning "Local server not responding on port 8000"
    fi
    
    # Test HTTPS
    if curl -s https://$DOMAIN/health > /dev/null; then
        print_success "HTTPS endpoint is working"
    else
        print_warning "HTTPS endpoint not responding"
        print_status "This might be normal if DNS propagation is still in progress"
    fi
    
    # Check service status
    if systemctl is-active --quiet ragpp-mcp-server.service; then
        print_success "RAG++ MCP service is running"
    else
        print_warning "RAG++ MCP service is not running"
        print_status "Check logs with: sudo journalctl -u ragpp-mcp-server.service -f"
    fi
}

# Display final information
show_final_info() {
    echo ""
    echo "🎉 MCP Server Setup Complete!"
    echo "============================="
    echo ""
    echo "📍 Your MCP server is now accessible at:"
    echo "   • HTTPS: https://$DOMAIN"
    echo "   • Health: https://$DOMAIN/health"
    echo "   • Docs: https://$DOMAIN/docs"
    echo "   • MCP Endpoint: https://$DOMAIN/mcp"
    echo ""
    echo "🔧 Service Management:"
    echo "   • Status: sudo systemctl status ragpp-mcp-server"
    echo "   • Logs: sudo journalctl -u ragpp-mcp-server -f"
    echo "   • Restart: sudo systemctl restart ragpp-mcp-server"
    echo ""
    echo "🔒 SSL Certificate:"
    echo "   • Auto-renewal enabled"
    echo "   • Check renewal: sudo certbot certificates"
    echo ""
    echo "🌐 MCP Client Configuration:"
    echo "   • Local MCP: Already configured in your settings"
    echo "   • Remote URL: https://$DOMAIN/mcp"
    echo "   • API Token: wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo"
    echo ""
    echo "📊 Testing Commands:"
    echo "   • curl https://$DOMAIN/health"
    echo "   • curl -H \"Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo\" https://$DOMAIN/search?q=test"
    echo ""
}

# Main execution
main() {
    check_sudo
    
    print_status "Starting MCP domain setup for $DOMAIN"
    
    # Run setup steps
    install_dependencies
    setup_firewall
    create_directories
    install_python_deps
    setup_ssl
    setup_nginx
    setup_systemd_service
    start_services
    test_setup
    
    show_final_info
    
    print_success "Setup completed successfully!"
}

# Run main function
main "$@"
