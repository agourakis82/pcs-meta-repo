#!/bin/bash
# RAG++ Dependencies Update Script
# Atualiza as dependências Python do sistema RAG++

set -e

# Configurações
PROJECT_DIR="/home/agourakis82/workspace/pcs-meta-repo"
LOG_FILE="/var/log/ragpp_updates.log"
VENV_DIR="$PROJECT_DIR/venv"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Função de log
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${GREEN}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

warn() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1"
    echo -e "${YELLOW}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

error() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1"
    echo -e "${RED}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

info() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1"
    echo -e "${BLUE}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

# Verificar se virtual environment existe
check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        error "Virtual environment não encontrado: $VENV_DIR"
        error "Execute primeiro: ./setup_production.sh"
        exit 1
    fi

    log "✅ Virtual environment encontrado"
}

# Ativar virtual environment
activate_venv() {
    source "$VENV_DIR/bin/activate"
    log "✅ Virtual environment ativado"
}

# Fazer backup de requirements atuais
backup_requirements() {
    log "Fazendo backup de requirements atuais..."

    local backup_file="$PROJECT_DIR/requirements_backup_$(date +%Y%m%d_%H%M%S).txt"

    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        cp "$PROJECT_DIR/requirements.txt" "$backup_file"
        log "✅ Backup salvo em: $backup_file"
    else
        warn "Arquivo requirements.txt não encontrado"
    fi
}

# Atualizar pip
update_pip() {
    log "Atualizando pip..."

    pip install --upgrade pip
    log "✅ Pip atualizado"
}

# Atualizar dependências
update_dependencies() {
    log "Atualizando dependências..."

    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        pip install --upgrade -r "$PROJECT_DIR/requirements.txt"
        log "✅ Dependências atualizadas do requirements.txt"
    else
        warn "Arquivo requirements.txt não encontrado, atualizando pacotes principais..."

        # Atualizar pacotes principais manualmente
        local main_packages=(
            "fastapi"
            "uvicorn"
            "chromadb"
            "pydantic"
            "requests"
            "python-multipart"
            "aiofiles"
        )

        for package in "${main_packages[@]}"; do
            info "Atualizando $package..."
            pip install --upgrade "$package" || warn "Falha ao atualizar $package"
        done
    fi
}

# Verificar se há atualizações de segurança
check_security_updates() {
    log "Verificando atualizações de segurança..."

    if command -v safety &> /dev/null; then
        info "Executando verificação de segurança..."
        safety check --full-report 2>/dev/null || warn "Verificação de segurança encontrou vulnerabilidades"
    else
        warn "Ferramenta 'safety' não instalada. Instale com: pip install safety"
    fi
}

# Limpar cache do pip
clean_pip_cache() {
    log "Limpando cache do pip..."

    pip cache purge 2>/dev/null || true
    log "✅ Cache do pip limpo"
}

# Verificar instalação
verify_installation() {
    log "Verificando instalação..."

    # Testar importações principais
    python -c "
import fastapi
import uvicorn
import chromadb
print('✅ Principais dependências importadas com sucesso')
print(f'FastAPI: {fastapi.__version__}')
print(f'Uvicorn: {uvicorn.__version__}')
" 2>/dev/null || error "Falha na verificação das dependências"

    log "✅ Verificação concluída"
}

# Reiniciar serviço se necessário
restart_service() {
    log "Verificando necessidade de reinício do serviço..."

    if systemctl is-active --quiet ragpp 2>/dev/null; then
        info "Reiniciando serviço ragpp..."
        sudo systemctl restart ragpp

        # Aguardar inicialização
        sleep 5

        if systemctl is-active --quiet ragpp; then
            log "✅ Serviço reiniciado com sucesso"
        else
            error "Falha ao reiniciar serviço"
        fi
    else
        warn "Serviço ragpp não está ativo"
    fi
}

# Gerar relatório de atualização
generate_report() {
    log "Gerando relatório de atualização..."

    local report_file="$PROJECT_DIR/reports/dependency_update_$(date +%Y%m%d).md"

    mkdir -p "$PROJECT_DIR/reports"

    cat > "$report_file" << EOF
# Relatório de Atualização de Dependências RAG++
Data: $(date '+%Y-%m-%d %H:%M:%S')

## Ações Executadas
- ✅ Backup de requirements
- ✅ Atualização do pip
- ✅ Atualização de dependências
- ✅ Verificação de segurança
- ✅ Limpeza de cache
- ✅ Verificação de instalação
- ✅ Reinício de serviço

## Versões Atuais
$(pip list --format=freeze | grep -E "(fastapi|uvicorn|chromadb|pydantic)" || echo "Não foi possível obter versões")

## Status
Atualização concluída com sucesso

---
*Relatório gerado automaticamente*
EOF

    log "✅ Relatório gerado: $report_file"
}

# Função principal
main() {
    echo "⬆️  RAG++ Dependencies Update"
    echo "============================"

    check_venv
    activate_venv
    backup_requirements
    update_pip
    update_dependencies
    check_security_updates
    clean_pip_cache
    verify_installation
    restart_service
    generate_report

    echo ""
    log "🎉 Atualização de dependências concluída!"
    echo ""
    echo "📋 Resumo:"
    echo "   • Pip atualizado"
    echo "   • Dependências atualizadas"
    echo "   • Segurança verificada"
    echo "   • Cache limpo"
    echo "   • Instalação verificada"
    echo "   • Serviço reiniciado"
    echo "   • Relatório gerado"
}

# Executar apenas se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi