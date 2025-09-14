#!/bin/bash

# Test Data Integration Script
# Testa a integração completa entre coleta de dados e alimentação do servidor

set -euo pipefail

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECT_SCRIPT="$SCRIPT_DIR/collect-7days-data.sh"
TEMP_DATA_DIR="/tmp/pcs-7days-analysis"
SERVER_URL="http://127.0.0.1:8000"
ADMIN_ENDPOINT="$SERVER_URL/admin/feed-analysis-data"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}✅ $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}" >&2
}

error() {
    echo -e "${RED}❌ $1${NC}" >&2
}

check_prerequisites() {
    log "Verificando pré-requisitos..."
    
    # Verificar se o script de coleta existe
    if [[ ! -f "$COLLECT_SCRIPT" ]]; then
        error "Script de coleta não encontrado: $COLLECT_SCRIPT"
        exit 1
    fi
    
    # Verificar se o script é executável
    if [[ ! -x "$COLLECT_SCRIPT" ]]; then
        warning "Tornando script executável..."
        chmod +x "$COLLECT_SCRIPT"
    fi
    
    # Verificar dependências
    local deps=("curl" "jq" "git")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error "Dependência não encontrada: $dep"
            exit 1
        fi
    done
    
    success "Pré-requisitos verificados"
}

check_server_health() {
    log "Verificando saúde do servidor..."
    
    # Tentar conectar ao servidor
    if ! curl -s --connect-timeout 5 "$SERVER_URL/health" > /dev/null; then
        error "Servidor não está respondendo em $SERVER_URL"
        error "Certifique-se de que o servidor RAG++ está rodando"
        exit 1
    fi
    
    success "Servidor está respondendo"
}

collect_data() {
    log "Executando coleta de dados dos últimos 7 dias..."
    
    # Limpar dados anteriores
    if [[ -d "$TEMP_DATA_DIR" ]]; then
        rm -rf "$TEMP_DATA_DIR"
    fi
    
    # Executar script de coleta
    if ! "$COLLECT_SCRIPT"; then
        error "Falha na coleta de dados"
        exit 1
    fi
    
    # Verificar se os dados foram gerados
    if [[ ! -d "$TEMP_DATA_DIR" ]]; then
        error "Diretório de dados não foi criado: $TEMP_DATA_DIR"
        exit 1
    fi
    
    local consolidated_report="$TEMP_DATA_DIR/consolidated-report.json"
    if [[ ! -f "$consolidated_report" ]]; then
        error "Relatório consolidado não foi gerado: $consolidated_report"
        exit 1
    fi
    
    success "Dados coletados com sucesso"
    log "Dados salvos em: $TEMP_DATA_DIR"
}

validate_data_structure() {
    log "Validando estrutura dos dados..."
    
    local consolidated_report="$TEMP_DATA_DIR/consolidated-report.json"
    
    # Verificar se é JSON válido
    if ! jq . "$consolidated_report" > /dev/null 2>&1; then
        error "Relatório consolidado não é um JSON válido"
        exit 1
    fi
    
    # Verificar campos obrigatórios
    local required_fields=(
        ".report_metadata"
        ".executive_summary"
        ".data_files"
    )
    
    for field in "${required_fields[@]}"; do
        if ! jq -e "$field" "$consolidated_report" > /dev/null 2>&1; then
            error "Campo obrigatório não encontrado: $field"
            exit 1
        fi
    done
    
    success "Estrutura dos dados validada"
}

send_data_to_server() {
    log "Enviando dados para o servidor..."
    
    local consolidated_report="$TEMP_DATA_DIR/consolidated-report.json"
    
    # Enviar dados via POST
    local response
    response=$(curl -s -w "%{http_code}" \
        -H "Content-Type: application/json" \
        -d "@$consolidated_report" \
        "$ADMIN_ENDPOINT")
    
    local http_code="${response: -3}"
    local response_body="${response%???}"
    
    if [[ "$http_code" -eq 200 ]]; then
        success "Dados enviados com sucesso"
        
        # Mostrar resumo da resposta
        if command -v jq &> /dev/null && echo "$response_body" | jq . > /dev/null 2>&1; then
            log "Resumo da resposta do servidor:"
            echo "$response_body" | jq -r '
                "Status: " + .status + 
                "\nMemórias armazenadas: " + (.memories_stored | tostring) +
                "\nPeríodo de análise: " + (.analysis_period_days | tostring) + " dias" +
                "\nCommits: " + (.summary.commits | tostring) +
                "\nErros nginx: " + (.summary.nginx_errors | tostring) +
                "\nServiços saudáveis: " + (.summary.services_healthy | tostring) +
                "\nAPI externa acessível: " + (.summary.external_api_accessible | tostring) +
                "\nAPI interna acessível: " + (.summary.internal_api_accessible | tostring)
            '
        else
            log "Resposta do servidor: $response_body"
        fi
    else
        error "Falha ao enviar dados. Código HTTP: $http_code"
        error "Resposta: $response_body"
        exit 1
    fi
}

verify_data_storage() {
    log "Verificando se os dados foram armazenados corretamente..."
    
    # Buscar por análise do sistema na memória
    local search_response
    search_response=$(curl -s "$SERVER_URL/memory/search?query=análise+sistema+7+dias&max_results=5")
    
    if echo "$search_response" | jq -e '.results | length > 0' > /dev/null 2>&1; then
        success "Dados encontrados na memória do servidor"
        
        local result_count
        result_count=$(echo "$search_response" | jq -r '.results | length')
        log "Encontradas $result_count memórias relacionadas"
        
        # Mostrar tipos de memória armazenados
        echo "$search_response" | jq -r '.results[].memory_type' | sort | uniq -c | while read -r count type; do
            log "  - $type: $count itens"
        done
    else
        warning "Dados não encontrados na busca de memória"
        warning "Isso pode ser normal se a indexação ainda estiver em progresso"
    fi
}

cleanup() {
    log "Limpando arquivos temporários..."
    
    if [[ -d "$TEMP_DATA_DIR" ]]; then
        rm -rf "$TEMP_DATA_DIR"
        success "Arquivos temporários removidos"
    fi
}

show_usage() {
    echo "Uso: $0 [opções]"
    echo ""
    echo "Opções:"
    echo "  --no-cleanup    Não remove arquivos temporários após o teste"
    echo "  --server-url    URL do servidor (padrão: $SERVER_URL)"
    echo "  --help          Mostra esta ajuda"
    echo ""
    echo "Este script testa a integração completa entre:"
    echo "1. Coleta de dados dos últimos 7 dias"
    echo "2. Validação da estrutura dos dados"
    echo "3. Envio para o endpoint do servidor"
    echo "4. Verificação do armazenamento na memória"
}

main() {
    local no_cleanup=false
    
    # Parse argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-cleanup)
                no_cleanup=true
                shift
                ;;
            --server-url)
                SERVER_URL="$2"
                ADMIN_ENDPOINT="$SERVER_URL/admin/feed-analysis-data"
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
    
    log "Iniciando teste de integração de dados..."
    log "Servidor: $SERVER_URL"
    log "Endpoint: $ADMIN_ENDPOINT"
    echo ""
    
    # Executar testes em sequência
    check_prerequisites
    check_server_health
    collect_data
    validate_data_structure
    send_data_to_server
    verify_data_storage
    
    if [[ "$no_cleanup" == "false" ]]; then
        cleanup
    else
        log "Arquivos temporários mantidos em: $TEMP_DATA_DIR"
    fi
    
    echo ""
    success "Teste de integração concluído com sucesso!"
    log "O servidor agora possui dados analíticos dos últimos 7 dias"
}

# Executar função principal se script for chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi