#!/bin/bash

# PCS AI-Enhanced Research Suite Master Control
# Unifies all research automation with advanced AI capabilities

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BASE_DIR="$SCRIPT_DIR"
readonly SCRIPTS_DIR="$BASE_DIR/scripts"

# Color output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Icons
readonly ROCKET="🚀"
readonly BRAIN="🧠"
readonly SEARCH="🔍"
readonly CHART="📊"
readonly BOOK="📚"
readonly GEAR="⚙️"
readonly CHECK="✅"
readonly CROSS="❌"
readonly WARNING="⚠️"

show_banner() {
    echo -e "${PURPLE}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                PCS AI-Enhanced Research Suite                ║
║           Computational-Symbolic Psychiatry v4.3             ║
║                                                               ║
║  🧠 AI-Powered Research  📊 Analytics  🔍 Multi-Engine Search ║
║  📚 Literature Synthesis  ⚙️ Automation  🚀 Nature HB Ready  ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

show_main_menu() {
    echo -e "${CYAN}${ROCKET} PCS AI Research Suite - Main Menu${NC}\n"
    
    echo -e "${GREEN}🧠 AI-ENHANCED RESEARCH${NC}"
    echo "  1) ${BRAIN} Intelligent Literature Search & Analysis"
    echo "  2) ${CHART} Generate Research Strategy (AI-Powered)"
    echo "  3) ${BOOK} Complete Research Pipeline (Full AI)"
    echo "  4) ${SEARCH} AI Gap Analysis & Recommendations"
    echo "  5) ${GEAR} Create Manuscript Outline (Nature HB)"
    echo ""
    
    echo -e "${YELLOW}📊 RESEARCH AUTOMATION${NC}"
    echo "  6) ${SEARCH} Multi-Engine Academic Search"
    echo "  7) ${CHART} Research Dashboard & Analytics" 
    echo "  8) ${BOOK} Literature Synthesis Report"
    echo "  9) ${GEAR} Zotero Integration & Citations"
    echo ""
    
    echo -e "${BLUE}🔧 SYSTEM MANAGEMENT${NC}"
    echo " 10) ${GEAR} Check System Status"
    echo " 11) ${CHART} View MCP Research Memory"
    echo " 12) ${BRAIN} Test AI Components"
    echo " 13) ${SEARCH} Quick Search (Legacy)"
    echo ""
    
    echo -e "${PURPLE}🚀 ADVANCED WORKFLOWS${NC}"
    echo " 14) ${ROCKET} Nature HB Publication Pipeline"
    echo " 15) ${BRAIN} AI Research Assistant (Direct)"
    echo " 16) ${CHART} Generate Publication Metrics"
    echo " 17) ${BOOK} Export Research Summary"
    echo ""
    
    echo "  q) Quit"
    echo ""
}

check_system_status() {
    echo -e "${BLUE}${GEAR} Checking System Status...${NC}\n"
    
    local status_ok=true
    
    # Check Python
    if command -v python3 &> /dev/null; then
        echo -e "${CHECK} Python 3: $(python3 --version)"
    else
        echo -e "${CROSS} Python 3: Not found"
        status_ok=false
    fi
    
    # Check Node.js (for MCP)
    if command -v node &> /dev/null; then
        echo -e "${CHECK} Node.js: $(node --version)"
    else
        echo -e "${CROSS} Node.js: Not found"
        status_ok=false
    fi
    
    # Check MCP Memory Server
    if pgrep -f "mcp-memory-server" > /dev/null; then
        echo -e "${CHECK} MCP Memory Server: Running"
    else
        echo -e "${WARNING} MCP Memory Server: Not running"
    fi
    
    # Check Gemini API
    if [[ -f "$HOME/.gemini/settings.json" ]]; then
        if jq -e '.apiKey' "$HOME/.gemini/settings.json" &> /dev/null; then
            echo -e "${CHECK} Gemini AI API: Configured"
        else
            echo -e "${CROSS} Gemini AI API: Key not found"
            status_ok=false
        fi
    else
        echo -e "${CROSS} Gemini AI API: Not configured"
        status_ok=false
    fi
    
    # Check critical scripts
    local scripts=(
        "memory_manager.py"
        "ai_research_assistant.py" 
        "intelligent_research_hub.py"
        "advanced_academic_hub.py"
        "research_dashboard.py"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$SCRIPTS_DIR/$script" ]]; then
            echo -e "${CHECK} $script: Available"
        else
            echo -e "${CROSS} $script: Missing"
            status_ok=false
        fi
    done
    
    echo ""
    if $status_ok; then
        echo -e "${GREEN}${CHECK} System Status: All systems operational${NC}"
    else
        echo -e "${RED}${CROSS} System Status: Some components need attention${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

run_intelligent_search() {
    echo -e "${BRAIN}${SEARCH} AI-Enhanced Literature Search${NC}\n"
    
    read -p "Enter research topic/question: " topic
    if [[ -z "$topic" ]]; then
        echo -e "${RED}${CROSS} No topic provided${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}${GEAR} Running intelligent search with AI analysis...${NC}"
    echo "This includes:"
    echo "- Multi-engine academic search"
    echo "- AI relevance analysis" 
    echo "- Literature synthesis"
    echo "- MCP memory storage"
    echo ""
    
    if python3 "$SCRIPTS_DIR/intelligent_research_hub.py" search "$topic"; then
        echo -e "\n${GREEN}${CHECK} Intelligent search completed successfully!${NC}"
    else
        echo -e "\n${RED}${CROSS} Search failed${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

generate_ai_strategy() {
    echo -e "${BRAIN}${CHART} AI-Powered Research Strategy Generator${NC}\n"
    
    read -p "Enter research goal: " goal
    if [[ -z "$goal" ]]; then
        echo -e "${RED}${CROSS} No goal provided${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}${GEAR} Generating comprehensive research strategy...${NC}"
    echo "AI will analyze:"
    echo "- Current literature landscape"
    echo "- Methodological approaches"
    echo "- Timeline and milestones"
    echo "- Risk assessment"
    echo "- Publication strategy"
    echo ""
    
    if python3 "$SCRIPTS_DIR/intelligent_research_hub.py" strategy "$goal"; then
        echo -e "\n${GREEN}${CHECK} Research strategy generated successfully!${NC}"
    else
        echo -e "\n${RED}${CROSS} Strategy generation failed${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

run_complete_ai_pipeline() {
    echo -e "${ROCKET}${BRAIN} Complete AI Research Pipeline${NC}\n"
    
    read -p "Enter main research objective: " objective
    if [[ -z "$objective" ]]; then
        echo -e "${RED}${CROSS} No objective provided${NC}"
        return 1
    fi
    
    echo -e "${PURPLE}${ROCKET} Starting complete AI research pipeline...${NC}"
    echo "This comprehensive workflow includes:"
    echo "1. Intelligent literature search & AI analysis"
    echo "2. AI-powered research strategy generation"
    echo "3. Automated gap analysis"
    echo "4. Nature HB manuscript outline"
    echo "5. Research metrics and recommendations"
    echo ""
    echo -e "${YELLOW}⏱️  Estimated time: 10-15 minutes${NC}"
    echo ""
    
    read -p "Continue with complete pipeline? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        if python3 "$SCRIPTS_DIR/intelligent_research_hub.py" pipeline "$objective"; then
            echo -e "\n${GREEN}${CHECK} Complete AI pipeline finished successfully!${NC}"
            echo -e "${CYAN}${CHART} Results stored in MCP memory for future reference${NC}"
        else
            echo -e "\n${RED}${CROSS} Pipeline failed${NC}"
        fi
    else
        echo -e "${YELLOW}${WARNING} Pipeline cancelled${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

run_ai_gap_analysis() {
    echo -e "${SEARCH}${CHART} AI-Powered Gap Analysis${NC}\n"
    
    echo -e "${YELLOW}${GEAR} Running comprehensive gap analysis...${NC}"
    echo "AI will analyze:"
    echo "- Current research coverage"
    echo "- Theoretical gaps"
    echo "- Methodological gaps"
    echo "- Publication opportunities"
    echo "- Priority recommendations"
    echo ""
    
    if python3 "$SCRIPTS_DIR/intelligent_research_hub.py" gaps; then
        echo -e "\n${GREEN}${CHECK} Gap analysis completed successfully!${NC}"
    else
        echo -e "\n${RED}${CROSS} Gap analysis failed${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

create_manuscript_outline() {
    echo -e "${BOOK}${GEAR} AI Manuscript Outline Generator${NC}\n"
    
    read -p "Enter manuscript focus/topic: " focus
    if [[ -z "$focus" ]]; then
        echo -e "${RED}${CROSS} No focus provided${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}${GEAR} Generating Nature Human Behaviour manuscript outline...${NC}"
    echo "AI will create:"
    echo "- Structured abstract"
    echo "- Detailed section outlines"
    echo "- Figure planning"
    echo "- Statistical analysis plan"
    echo "- Timeline for completion"
    echo ""
    
    if python3 "$SCRIPTS_DIR/intelligent_research_hub.py" outline "$focus"; then
        echo -e "\n${GREEN}${CHECK} Manuscript outline created successfully!${NC}"
    else
        echo -e "\n${RED}${CROSS} Outline generation failed${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

run_academic_search() {
    echo -e "${SEARCH}${BOOK} Multi-Engine Academic Search${NC}\n"
    
    read -p "Enter search query: " query
    if [[ -z "$query" ]]; then
        echo -e "${RED}${CROSS} No query provided${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}${GEAR} Running academic search across multiple engines...${NC}"
    
    if python3 "$SCRIPTS_DIR/advanced_academic_hub.py" "$query"; then
        echo -e "\n${GREEN}${CHECK} Academic search completed!${NC}"
    else
        echo -e "\n${RED}${CROSS} Search failed${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

generate_research_dashboard() {
    echo -e "${CHART}${GEAR} Research Dashboard & Analytics${NC}\n"
    
    echo -e "${YELLOW}${GEAR} Generating research dashboard...${NC}"
    
    if python3 "$SCRIPTS_DIR/research_dashboard.py"; then
        echo -e "\n${GREEN}${CHECK} Dashboard generated successfully!${NC}"
        if [[ -f "research_dashboard.html" ]]; then
            echo -e "${CYAN}${CHART} Dashboard saved as: research_dashboard.html${NC}"
        fi
    else
        echo -e "\n${RED}${CROSS} Dashboard generation failed${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

view_mcp_memory() {
    echo -e "${BOOK}${CHART} MCP Research Memory${NC}\n"
    
    echo -e "${YELLOW}${GEAR} Retrieving research context from MCP...${NC}"
    
    if python3 "$SCRIPTS_DIR/intelligent_research_hub.py" status; then
        echo -e "\n${GREEN}${CHECK} Research memory retrieved successfully!${NC}"
    else
        echo -e "\n${RED}${CROSS} Memory retrieval failed${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

test_ai_components() {
    echo -e "${BRAIN}${GEAR} AI Components Test${NC}\n"
    
    echo -e "${YELLOW}${GEAR} Testing AI research components...${NC}"
    echo ""
    
    # Test Gemini API
    echo "1. Testing Gemini AI API..."
    if [[ -f "$HOME/.gemini/settings.json" ]] && jq -e '.apiKey' "$HOME/.gemini/settings.json" &> /dev/null; then
        echo -e "${CHECK} Gemini API: Configured"
    else
        echo -e "${CROSS} Gemini API: Not configured"
    fi
    
    # Test AI Assistant
    echo "2. Testing AI Research Assistant..."
    if python3 "$SCRIPTS_DIR/ai_research_assistant.py" --help &> /dev/null; then
        echo -e "${CHECK} AI Research Assistant: Available"
    else
        echo -e "${CROSS} AI Research Assistant: Not working"
    fi
    
    # Test Intelligence Hub
    echo "3. Testing Intelligent Research Hub..."
    if python3 "$SCRIPTS_DIR/intelligent_research_hub.py" --help &> /dev/null; then
        echo -e "${CHECK} Intelligent Research Hub: Available"
    else
        echo -e "${CROSS} Intelligent Research Hub: Not working"
    fi
    
    # Test MCP Integration
    echo "4. Testing MCP Integration..."
    if python3 "$SCRIPTS_DIR/memory_manager.py" --help &> /dev/null; then
        echo -e "${CHECK} MCP Memory Manager: Available"
    else
        echo -e "${CROSS} MCP Memory Manager: Not working"
    fi
    
    echo ""
    echo -e "${GREEN}${CHECK} AI components test completed${NC}"
    
    read -p "Press Enter to continue..."
}

run_nature_hb_pipeline() {
    echo -e "${ROCKET}${BOOK} Nature Human Behaviour Publication Pipeline${NC}\n"
    
    read -p "Enter research topic for Nature HB: " topic
    if [[ -z "$topic" ]]; then
        echo -e "${RED}${CROSS} No topic provided${NC}"
        return 1
    fi
    
    echo -e "${PURPLE}${ROCKET} Starting Nature HB publication pipeline...${NC}"
    echo "This specialized workflow includes:"
    echo "1. High-impact literature review"
    echo "2. Nature HB-specific methodology"
    echo "3. Publication-ready outline"
    echo "4. Statistical analysis plan"
    echo "5. Submission timeline"
    echo ""
    
    # Run comprehensive pipeline with Nature HB focus
    if python3 "$SCRIPTS_DIR/intelligent_research_hub.py" pipeline "$topic"; then
        echo -e "\n${GREEN}${CHECK} Nature HB pipeline completed!${NC}"
        
        # Generate specific outline
        echo -e "${YELLOW}${GEAR} Creating Nature HB manuscript outline...${NC}"
        if python3 "$SCRIPTS_DIR/intelligent_research_hub.py" outline "$topic"; then
            echo -e "${GREEN}${CHECK} Manuscript outline ready for Nature HB!${NC}"
        fi
    else
        echo -e "\n${RED}${CROSS} Pipeline failed${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

quick_search() {
    echo -e "${SEARCH}${GEAR} Quick Legacy Search${NC}\n"
    
    read -p "Enter search query: " query
    if [[ -z "$query" ]]; then
        echo -e "${RED}${CROSS} No query provided${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}${GEAR} Running quick search...${NC}"
    
    # Use original quick search
    bash "$BASE_DIR/pcs_research_suite.sh" quick "$query"
    
    read -p "Press Enter to continue..."
}

main() {
    while true; do
        clear
        show_banner
        show_main_menu
        
        read -p "Select option [1-17, q]: " choice
        echo ""
        
        case $choice in
            1) run_intelligent_search ;;
            2) generate_ai_strategy ;;
            3) run_complete_ai_pipeline ;;
            4) run_ai_gap_analysis ;;
            5) create_manuscript_outline ;;
            6) run_academic_search ;;
            7) generate_research_dashboard ;;
            8) echo "Literature synthesis - Use option 1 or 3 for AI-enhanced synthesis" ;;
            9) echo "Zotero integration - Available in advanced workflows" ;;
            10) check_system_status ;;
            11) view_mcp_memory ;;
            12) test_ai_components ;;
            13) quick_search ;;
            14) run_nature_hb_pipeline ;;
            15) 
                echo -e "${BRAIN} AI Research Assistant Direct Access${NC}"
                echo "Usage: python3 scripts/ai_research_assistant.py [analyze|strategy|synthesize|outline|gaps] --topic 'your topic'"
                read -p "Press Enter to continue..."
                ;;
            16)
                echo -e "${CHART} Publication Metrics Generator${NC}"
                echo "Use option 7 (Research Dashboard) for comprehensive metrics"
                read -p "Press Enter to continue..."
                ;;
            17)
                echo -e "${BOOK} Research Summary Export${NC}"
                echo "Use option 11 (View MCP Memory) for current research summary"
                read -p "Press Enter to continue..."
                ;;
            q|Q) 
                echo -e "${GREEN}${CHECK} Thank you for using PCS AI Research Suite!${NC}"
                echo -e "${CYAN}🧠 Keep advancing computational psychiatry research! 🚀${NC}"
                exit 0 
                ;;
            *) 
                echo -e "${RED}${CROSS} Invalid option. Please try again.${NC}"
                read -p "Press Enter to continue..."
                ;;
        esac
    done
}

# Handle script arguments for automation
if [[ $# -gt 0 ]]; then
    case "$1" in
        "ai-search")
            shift
            python3 "$SCRIPTS_DIR/intelligent_research_hub.py" search "$@"
            ;;
        "ai-strategy")
            shift
            python3 "$SCRIPTS_DIR/intelligent_research_hub.py" strategy "$@"
            ;;
        "ai-pipeline")
            shift
            python3 "$SCRIPTS_DIR/intelligent_research_hub.py" pipeline "$@"
            ;;
        "ai-gaps")
            python3 "$SCRIPTS_DIR/intelligent_research_hub.py" gaps
            ;;
        "ai-outline")
            shift
            python3 "$SCRIPTS_DIR/intelligent_research_hub.py" outline "$@"
            ;;
        "status")
            check_system_status
            ;;
        "test")
            test_ai_components
            ;;
        *)
            echo "Usage: $0 [ai-search|ai-strategy|ai-pipeline|ai-gaps|ai-outline|status|test] [args...]"
            echo "Or run without arguments for interactive menu"
            exit 1
            ;;
    esac
else
    main
fi
