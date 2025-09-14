#!/bin/bash
# PCS AI Research Suite - Build & Install Script
# Compila, instala e cria atalhos para a interface gráfica

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/pcs-ai-suite"
DESKTOP_DIR="$HOME/.local/share/applications"
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons"

print_header() {
    echo -e "${BLUE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                PCS AI Research Suite v4.3                   ║
║                 Build & Install System                      ║
║                                                              ║
║           Computational-Symbolic Psychiatry                 ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    print_status "Checking build dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        exit 1
    fi
    print_success "Python 3: $(python3 --version)"
    
    # Check Tkinter
    if ! python3 -c "import tkinter" 2>/dev/null; then
        print_error "Tkinter not available"
        print_status "Install with: sudo apt-get install python3-tk"
        exit 1
    fi
    print_success "Tkinter: Available"
    
    # Check required directories exist
    for script in "scripts/pcs_gui.py" "scripts/pcs_clean_gui.py" "scripts/pcs_demo_gui.py"; do
        if [[ ! -f "$SCRIPT_DIR/$script" ]]; then
            print_error "Missing: $script"
            exit 1
        fi
    done
    print_success "GUI Scripts: Available"
}

create_icon() {
    print_status "Creating application icon..."
    
    mkdir -p "$ICON_DIR"
    
    # Create a simple SVG icon
    cat > "$ICON_DIR/pcs-ai-suite.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect width="64" height="64" rx="8" fill="#2E86AB"/>
  <circle cx="32" cy="20" r="8" fill="white"/>
  <rect x="20" y="32" width="24" height="4" fill="white"/>
  <rect x="16" y="40" width="32" height="4" fill="white"/>
  <rect x="24" y="48" width="16" height="4" fill="white"/>
  <text x="32" y="58" text-anchor="middle" fill="white" font-family="Arial" font-size="8">AI</text>
</svg>
EOF
    
    # Convert to PNG if possible
    if command -v convert &> /dev/null; then
        convert "$ICON_DIR/pcs-ai-suite.svg" "$ICON_DIR/pcs-ai-suite.png"
        print_success "Icon created: PNG format"
    else
        print_success "Icon created: SVG format"
    fi
}

build_executable() {
    print_status "Building executable launcher..."
    
    mkdir -p "$BIN_DIR"
    
    # Create main executable
    cat > "$BIN_DIR/pcs-ai-suite" << EOF
#!/bin/bash
# PCS AI Research Suite - Main Launcher
cd "$SCRIPT_DIR"
exec python3 scripts/pcs_clean_gui.py "\$@"
EOF
    
    # Create variants
    cat > "$BIN_DIR/pcs-ai-suite-full" << EOF
#!/bin/bash
# PCS AI Research Suite - Full Version
cd "$SCRIPT_DIR"
exec python3 scripts/pcs_gui.py "\$@"
EOF
    
    cat > "$BIN_DIR/pcs-ai-suite-demo" << EOF
#!/bin/bash
# PCS AI Research Suite - Demo Version
cd "$SCRIPT_DIR"
exec python3 scripts/pcs_demo_gui.py "\$@"
EOF
    
    # Make executable
    chmod +x "$BIN_DIR/pcs-ai-suite"
    chmod +x "$BIN_DIR/pcs-ai-suite-full"
    chmod +x "$BIN_DIR/pcs-ai-suite-demo"
    
    print_success "Executables created in $BIN_DIR"
}

create_desktop_entry() {
    print_status "Creating desktop entries..."
    
    mkdir -p "$DESKTOP_DIR"
    
    # Main desktop entry
    cat > "$DESKTOP_DIR/pcs-ai-suite.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PCS AI Research Suite
Comment=AI-Enhanced Research Automation for Computational Psychiatry
Exec=$BIN_DIR/pcs-ai-suite
Icon=$ICON_DIR/pcs-ai-suite
Terminal=false
Categories=Education;Science;Development;
Keywords=AI;Research;Psychiatry;Academic;Literature;
StartupNotify=true
EOF
    
    # Full version entry
    cat > "$DESKTOP_DIR/pcs-ai-suite-full.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PCS AI Research Suite (Full)
Comment=Complete AI Research Interface with All Features
Exec=$BIN_DIR/pcs-ai-suite-full
Icon=$ICON_DIR/pcs-ai-suite
Terminal=false
Categories=Education;Science;Development;
Keywords=AI;Research;Psychiatry;Academic;Literature;
StartupNotify=true
EOF
    
    # Demo version entry
    cat > "$DESKTOP_DIR/pcs-ai-suite-demo.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PCS AI Research Suite (Demo)
Comment=Lightweight Demo Version of AI Research Suite
Exec=$BIN_DIR/pcs-ai-suite-demo
Icon=$ICON_DIR/pcs-ai-suite
Terminal=false
Categories=Education;Science;Development;
Keywords=AI;Research;Psychiatry;Academic;Literature;
StartupNotify=true
EOF
    
    # Make desktop files executable
    chmod +x "$DESKTOP_DIR"/*.desktop
    
    # Update desktop database if available
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$DESKTOP_DIR"
        print_success "Desktop database updated"
    fi
    
    print_success "Desktop entries created"
}

install_to_applications_menu() {
    print_status "Installing to applications menu..."
    
    # Copy to system applications if we have permissions
    if [[ -w "/usr/share/applications" ]]; then
        sudo cp "$DESKTOP_DIR"/*.desktop /usr/share/applications/
        sudo update-desktop-database /usr/share/applications/
        print_success "Installed to system applications menu"
    else
        print_warning "No system permissions - installed to user applications only"
    fi
}

create_makefile_targets() {
    print_status "Adding Makefile targets..."
    
    # Check if Makefile exists and add our targets
    if [[ -f "$SCRIPT_DIR/Makefile" ]]; then
        # Add GUI targets to Makefile if not already present
        if ! grep -q "gui-install" "$SCRIPT_DIR/Makefile"; then
            cat >> "$SCRIPT_DIR/Makefile" << 'EOF'

# ==========================
# GUI Build & Install
# ==========================

.PHONY: gui-install gui-uninstall gui-run gui-run-demo gui-run-full

gui-install:
	@echo "[make] Installing PCS AI Research Suite GUI..."
	@./build_install.sh

gui-uninstall:
	@echo "[make] Uninstalling PCS AI Research Suite GUI..."
	@rm -f ~/.local/bin/pcs-ai-suite*
	@rm -f ~/.local/share/applications/pcs-ai-suite*.desktop
	@rm -f ~/.local/share/icons/pcs-ai-suite.*
	@echo "[make] GUI uninstalled"

gui-run:
	@echo "[make] Launching PCS AI Research Suite (Clean)..."
	@python3 scripts/pcs_clean_gui.py

gui-run-demo:
	@echo "[make] Launching PCS AI Research Suite (Demo)..."
	@python3 scripts/pcs_demo_gui.py

gui-run-full:
	@echo "[make] Launching PCS AI Research Suite (Full)..."
	@python3 scripts/pcs_gui.py

EOF
            print_success "Makefile targets added"
        else
            print_warning "Makefile targets already exist"
        fi
    fi
}

show_installation_summary() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    INSTALLATION COMPLETE                    ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Available Commands:${NC}"
    echo "  pcs-ai-suite         - Launch clean version (recommended)"
    echo "  pcs-ai-suite-full    - Launch full version with emojis"
    echo "  pcs-ai-suite-demo    - Launch lightweight demo"
    echo ""
    echo -e "${YELLOW}Makefile Targets:${NC}"
    echo "  make gui-run         - Run clean version"
    echo "  make gui-run-full    - Run full version"
    echo "  make gui-run-demo    - Run demo version"
    echo "  make gui-install     - Reinstall GUI"
    echo "  make gui-uninstall   - Remove GUI installation"
    echo ""
    echo -e "${YELLOW}Desktop Integration:${NC}"
    echo "  - Applications menu: Search for 'PCS AI Research Suite'"
    echo "  - Desktop files: ~/.local/share/applications/"
    echo "  - Executables: ~/.local/bin/"
    echo "  - Icon: ~/.local/share/icons/"
    echo ""
    echo -e "${BLUE}To start using:${NC}"
    echo "  1. Open terminal and type: pcs-ai-suite"
    echo "  2. Or find 'PCS AI Research Suite' in your applications menu"
    echo "  3. Or run: make gui-run"
    echo ""
}

uninstall() {
    print_status "Uninstalling PCS AI Research Suite..."
    
    rm -f "$BIN_DIR/pcs-ai-suite"*
    rm -f "$DESKTOP_DIR/pcs-ai-suite"*.desktop
    rm -f "$ICON_DIR/pcs-ai-suite".*
    
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$DESKTOP_DIR"
    fi
    
    print_success "Uninstallation complete"
}

main() {
    print_header
    
    case "${1:-install}" in
        install)
            check_dependencies
            create_icon
            build_executable
            create_desktop_entry
            install_to_applications_menu
            create_makefile_targets
            show_installation_summary
            ;;
        uninstall)
            uninstall
            ;;
        --help|-h)
            echo "Usage: $0 [install|uninstall]"
            echo ""
            echo "Commands:"
            echo "  install     - Build and install GUI (default)"
            echo "  uninstall   - Remove GUI installation"
            echo "  --help      - Show this help"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
}

main "$@"
