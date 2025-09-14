#!/bin/bash

# Feed Server Pipeline Script
# Script principal para alimentar o servidor com dados dos últimos 7 dias

set -euo pipefail

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COLLECT_SCRIPT="$SCRIPT_DIR/collect-7days-data.sh"
TEST_SCRIPT="$SCRIPT_DIR/test-data-integration.sh"
SERVER_URL="http://127.0.0.1:8000"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

banner() {
    echo -e "${BOLD}${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                  FEED SERVER PIPELINE                        ║"
    echo "║           Alimentação do Servidor com Dados 7 Dias           ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_server_status() {
    log "Verificando status do servidor RAG++..."
    
    # Verificar se o servidor está rodando
    if ! curl -s --connect-timeout 5 "$SERVER_URL/health" > /dev/null; then
        warning "Servidor não está respondendo. Tentando iniciar..."
        
        # Tentar iniciar o servidor
        if [[ -f "$PROJECT_ROOT/ragpp/ragpp_web_server.py" ]]; then
            log "Iniciando servidor RAG++..."
            cd "$PROJECT_ROOT"
            
            # Verificar se uvicorn está disponível
            if command -v uvicorn &> /dev/null; then
                nohup uvicorn ragpp.ragpp_web_server:app --host 127.0.0.1 --port 8000 \
                    --log-level info > /tmp/ragpp-server.log 2>&1 &
                echo $! > /tmp/ragpp-server.pid
                
                # Aguardar o servidor inicializar
                local attempts=0
                while [[ $attempts -lt 30 ]]; do
                    if curl -s --connect-timeout 2 "$SERVER_URL/health" > /dev/null; then
                        success "Servidor iniciado com sucesso"
                        return 0
                    fi
                    sleep 2
                    ((attempts++))
                done
                
                error "Servidor não conseguiu inicializar dentro do tempo limite"
                return 1
            else
                error "uvicorn não encontrado. Instale com: pip install uvicorn"
                return 1
            fi
        else
            error "Arquivo do servidor não encontrado: $PROJECT_ROOT/ragpp/ragpp_web_server.py"
            return 1
        fi
    else
        success "Servidor já está rodando"
        return 0
    fi
}

run_data_collection() {
    log "Executando coleta de dados dos últimos 7 dias..."
    
    if [[ ! -f "$COLLECT_SCRIPT" ]]; then
        error "Script de coleta não encontrado: $COLLECT_SCRIPT"
        return 1
    fi
    
    if ! "$COLLECT_SCRIPT"; then
        error "Falha na coleta de dados"
        return 1
    fi
    
    success "Coleta de dados concluída"
    return 0
}

feed_server() {
    log "Alimentando servidor com dados coletados..."
    
    # Procurar pelo arquivo de relatório consolidado mais recente
    local consolidated_report
    consolidated_report=$(find /tmp/pcs-7days-analysis/ -name "consolidated_report_*.json" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [[ ! -f "$consolidated_report" ]]; then
        error "Relatório consolidado não encontrado em /tmp/pcs-7days-analysis/"
        log "Arquivos disponíveis:"
        ls -la /tmp/pcs-7days-analysis/ 2>/dev/null || log "Diretório não existe"
        return 1
    fi
    
    log "Usando relatório: $(basename "$consolidated_report")"
    
    # Enviar dados para o servidor
    local response
    response=$(curl -s -w "%{http_code}" \
        -H "Content-Type: application/json" \
        -d "@$consolidated_report" \
        "$SERVER_URL/admin/feed-analysis-data" 2>/dev/null)
    
    local http_code="${response: -3}"
    local response_body="${response%???}"
    
    if [[ "$http_code" -eq 200 ]]; then
        success "Dados enviados com sucesso para o servidor"
        
        # Mostrar resumo se possível
        if command -v jq &> /dev/null && echo "$response_body" | jq . > /dev/null 2>&1; then
            local memories_stored
            memories_stored=$(echo "$response_body" | jq -r '.memories_stored // "N/A"')
            local period_days
            period_days=$(echo "$response_body" | jq -r '.analysis_period_days // "N/A"')
            
            log "Memórias armazenadas: $memories_stored"
            log "Período analisado: $period_days dias"
        fi
        
        return 0
    else
        error "Falha ao enviar dados. HTTP $http_code: $response_body"
        return 1
    fi
}

verify_integration() {
    log "Verificando integração dos dados..."
    
    # Buscar dados na memória do servidor
    local search_response
    search_response=$(curl -s "$SERVER_URL/memory/search?query=análise+sistema+7+dias&max_results=3" 2>/dev/null)
    
    if echo "$search_response" | jq -e '.results | length > 0' > /dev/null 2>&1; then
        success "Dados integrados com sucesso na memória do servidor"
        
        local result_count
        result_count=$(echo "$search_response" | jq -r '.results | length')
        log "Encontradas $result_count memórias relacionadas"
        
        return 0
    else
        warning "Dados não encontrados na busca (pode estar indexando)"
        return 0
    fi
}

cleanup() {
    log "Limpando arquivos temporários..."
    
    if [[ -d "/tmp/pcs-7days-analysis" ]]; then
        rm -rf "/tmp/pcs-7days-analysis"
        success "Arquivos temporários removidos"
    fi
}

show_summary() {
    echo ""
    echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${GREEN}                    PIPELINE CONCLUÍDO                        ${NC}"
    echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}O servidor RAG++ foi alimentado com os dados dos últimos 7 dias:${NC}"
    echo ""
    echo "📊 Dados coletados:"
    echo "   • Histórico de commits Git"
    echo "   • Logs do sistema (nginx, cloudflared)"
    echo "   • Métricas de performance"
    echo "   • Análise de erros"
    echo "   • Mudanças de configuração"
    echo ""
    echo "🧠 Memórias criadas:"
    echo "   • Resumo executivo do sistema"
    echo "   • Análise de conectividade e saúde"
    echo "   • Atividade de desenvolvimento"
    echo "   • Análise de erros"
    echo "   • Dados brutos para referência"
    echo ""
    echo "🌐 Servidor acessível em:"
    echo "   • API: $SERVER_URL"
    echo "   • Health: $SERVER_URL/health"
    echo "   • Memory Search: $SERVER_URL/memory/search"
    echo ""
    echo -e "${YELLOW}O servidor agora possui contexto histórico para melhor tomada de decisões!${NC}"
    echo ""
}

show_usage() {
    echo "Uso: $0 [opções]"
    echo ""
    echo "Opções:"
    echo "  --no-cleanup     Não remove arquivos temporários"
    echo "  --test-only      Executa apenas teste de integração"
    echo "  --collect-only   Executa apenas coleta de dados"
    echo "  --server-url     URL do servidor (padrão: $SERVER_URL)"
    echo "  --help           Mostra esta ajuda"
    echo ""
    echo "Este script executa o pipeline completo de alimentação do servidor:"
    echo "1. Verifica status do servidor RAG++"
    echo "2. Coleta dados dos últimos 7 dias"
    echo "3. Alimenta o servidor com os dados"
    echo "4. Verifica a integração"
    echo "5. Limpa arquivos temporários"
}

main() {
    local no_cleanup=false
    local test_only=false
    local collect_only=false
    
    # Parse argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-cleanup)
                no_cleanup=true
                shift
                ;;
            --test-only)
                test_only=true
                shift
                ;;
            --collect-only)
                collect_only=true
                shift
                ;;
            --server-url)
                SERVER_URL="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                error "Opção desconhecida: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    banner
    
    # Executar apenas teste se solicitado
    if [[ "$test_only" == "true" ]]; then
        log "Executando apenas teste de integração..."
        if [[ -f "$TEST_SCRIPT" ]]; then
            exec "$TEST_SCRIPT" ${no_cleanup:+--no-cleanup} --server-url "$SERVER_URL"
        else
            error "Script de teste não encontrado: $TEST_SCRIPT"
            exit 1
        fi
    fi
    
    # Executar apenas coleta se solicitado
    if [[ "$collect_only" == "true" ]]; then
        log "Executando apenas coleta de dados..."
        run_data_collection
        if [[ "$no_cleanup" == "false" ]]; then
            cleanup
        fi
        exit 0
    fi
    
    # Pipeline completo
    log "Iniciando pipeline completo de alimentação do servidor..."
    echo ""
    
    # Etapa 1: Verificar servidor
    if ! check_server_status; then
        error "Não foi possível garantir que o servidor esteja rodando"
        exit 1
    fi
    
    # Etapa 2: Coletar dados
    if ! run_data_collection; then
        error "Falha na coleta de dados"
        exit 1
    fi
    
    # Etapa 3: Alimentar servidor
    if ! feed_server; then
        error "Falha ao alimentar servidor"
        exit 1
    fi
    
    # Etapa 4: Verificar integração
    verify_integration
    
    # Etapa 5: Limpar temporários
    if [[ "$no_cleanup" == "false" ]]; then
        cleanup
    else
        log "Arquivos temporários mantidos em /tmp/pcs-7days-analysis"
    fi
    
    # Mostrar resumo final
    show_summary
}

# Trap para cleanup em caso de erro
trap 'error "Pipeline interrompido"; cleanup; exit 1' INT TERM

# Executar se script for chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi