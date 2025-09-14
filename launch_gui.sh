#!/bin/bash

# PCS AI Research Suite - GUI Launcher
# Launches the graphical user interface for the research suite

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BASE_DIR="$SCRIPT_DIR"
readonly GUI_SCRIPT="$BASE_DIR/scripts/pcs_gui.py"
readonly DEMO_SCRIPT="$BASE_DIR/scripts/pcs_demo_gui.py"
readonly CLEAN_SCRIPT="$BASE_DIR/scripts/pcs_clean_gui.py"

# Colors
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m' # No Color

show_banner() {
    echo -e "${BLUE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                    PCS GUI Launcher v4.3                    ║
║              Computational-Symbolic Psychiatry              ║
║                                                              ║
║  Graphical User Interface for AI Research Automation        ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

check_dependencies() {
    echo -e "${YELLOW}🔍 Checking dependencies...${NC}"
    
    local deps_ok=true
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        deps_ok=false
    else
        echo -e "${GREEN}✅ Python 3: $(python3 --version)${NC}"
    fi
    
    # Check Tkinter
    if ! python3 -c "import tkinter" 2>/dev/null; then
        echo -e "${RED}❌ Tkinter not available${NC}"
        echo -e "${YELLOW}💡 Install with: sudo apt-get install python3-tk${NC}"
        deps_ok=false
    else
        echo -e "${GREEN}✅ Tkinter: Available${NC}"
    fi
    
    # Check GUI script
    if [[ ! -f "$GUI_SCRIPT" ]]; then
        echo -e "${RED}❌ GUI script not found: $GUI_SCRIPT${NC}"
        deps_ok=false
    else
        echo -e "${GREEN}✅ GUI Script: Available${NC}"
    fi
    
    # Check AI suite
    if [[ ! -f "$BASE_DIR/pcs_ai_suite.sh" ]]; then
        echo -e "${YELLOW}⚠️  AI Suite script not found (some features may be limited)${NC}"
    else
        echo -e "${GREEN}✅ AI Suite: Available${NC}"
    fi
    
    if ! $deps_ok; then
        echo -e "\n${RED}❌ Some dependencies are missing. Please install them before running the GUI.${NC}"
        return 1
    fi
    
    echo -e "\n${GREEN}✅ All dependencies satisfied!${NC}"
    return 0
}

launch_gui() {
    echo -e "${BLUE}🚀 Launching PCS AI Research Suite GUI...${NC}"
    echo -e "${YELLOW}💡 Close the GUI window to return to terminal${NC}\n"
    
    cd "$BASE_DIR"
    
    # Launch the GUI
    if python3 "$GUI_SCRIPT"; then
        echo -e "\n${GREEN}✅ GUI closed successfully${NC}"
    else
        echo -e "\n${RED}❌ GUI encountered an error${NC}"
        return 1
    fi
}

launch_demo() {
    echo -e "${GREEN}Launching Demo GUI...${NC}"
    
    # Launch the demo GUI
    demo_script="$BASE_DIR/scripts/pcs_demo_gui.py"
    if python3 "$demo_script"; then
        echo -e "
${GREEN}Demo closed successfully${NC}"
    else
        echo -e "
${RED}Demo encountered an error${NC}"
        return 1
    fi
}

launch_clean() {
    echo -e "${GREEN}Launching Clean GUI (No Emojis)...${NC}"
    
    # Launch the clean GUI
    clean_script="$BASE_DIR/scripts/pcs_clean_gui.py"
    if python3 "$clean_script"; then
        echo -e "
${GREEN}Clean GUI closed successfully${NC}"
    else
        echo -e "
${RED}Clean GUI encountered an error${NC}"
        return 1
    fi
}

show_help() {
    echo -e "${BLUE}PCS GUI Launcher - Help${NC}\n"
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --demo         Launch demo version (lightweight)"
    echo "  --clean        Launch clean version (no emojis)"
    echo "  --check-deps   Check dependencies only"
    echo "  --help         Show this help message"
    echo "  (no options)   Launch the full GUI"
    echo ""
    echo -e "${YELLOW}Features:${NC}"
    echo "• AI-Enhanced Research Automation"
    echo "• Multi-Engine Literature Search"  
    echo "• Research Strategy Generation"
    echo "• Manuscript Outline Creation"
    echo "• Gap Analysis & Recommendations"
    echo "• MCP Memory Management"
    echo "• System Status Monitoring"
    echo ""
    echo -e "${YELLOW}Requirements:${NC}"
    echo "• Python 3.7+"
    echo "• Tkinter (python3-tk)"
    echo "• Gemini API configured"
    echo "• MCP Memory Server"
}

main() {
    case "${1:-}" in
        --demo)
            show_banner
            if check_dependencies; then
                echo ""
                launch_demo
            fi
            ;;
        --clean)
            show_banner
            if check_dependencies; then
                echo ""
                launch_clean
            fi
            ;;
        --check-deps)
            show_banner
            check_dependencies
            ;;
        --help|-h)
            show_help
            ;;
        "")
            show_banner
            if check_dependencies; then
                echo ""
                launch_gui
            fi
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
}

main "$@"
