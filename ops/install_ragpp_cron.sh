#!/bin/bash
# RAG++ Cron Jobs Installer
# Instala automaticamente os cron jobs para manutenção do sistema

set -e

# Configurações
PROJECT_DIR="/home/agourakis82/workspace/pcs-meta-repo"
CRON_CONF="$PROJECT_DIR/ragpp_cron.conf"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Função de log
log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

# Verificar se arquivo de configuração existe
check_config() {
    if [ ! -f "$CRON_CONF" ]; then
        error "Arquivo de configuração não encontrado: $CRON_CONF"
        exit 1
    fi

    log "✅ Arquivo de configuração encontrado"
}

# Fazer backup do crontab atual
backup_crontab() {
    log "Fazendo backup do crontab atual..."

    local backup_file="$PROJECT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S)"

    if crontab -l > "$backup_file" 2>/dev/null; then
        log "✅ Backup do crontab salvo em: $backup_file"
    else
        warn "Nenhum crontab existente encontrado (isso é normal para primeira instalação)"
    fi
}

# Instalar cron jobs
install_cron_jobs() {
    log "Instalando cron jobs..."

    # Combinar crontab atual com novos jobs
    local temp_cron="/tmp/ragpp_cron_temp"

    # Obter crontab atual
    crontab -l 2>/dev/null > "$temp_cron" || echo "" > "$temp_cron"

    # Adicionar comentário de identificação
    echo "" >> "$temp_cron"
    echo "# RAG++ Automated Maintenance Jobs" >> "$temp_cron"
    echo "# Installed on: $(date)" >> "$temp_cron"
    echo "" >> "$temp_cron"

    # Adicionar novos jobs
    cat "$CRON_CONF" >> "$temp_cron"

    # Instalar novo crontab
    crontab "$temp_cron"

    # Limpar arquivo temporário
    rm -f "$temp_cron"

    log "✅ Cron jobs instalados com sucesso"
}

# Verificar instalação
verify_installation() {
    log "Verificando instalação..."

    local installed_jobs=$(crontab -l | grep -c "ragpp" || echo "0")

    if [ "$installed_jobs" -gt 0 ]; then
        log "✅ $installed_jobs cron jobs instalados"
    else
        error "Nenhum cron job foi instalado"
        exit 1
    fi

    # Mostrar jobs instalados
    echo ""
    info "Cron jobs instalados:"
    crontab -l | grep -A 20 "RAG++" || crontab -l | tail -10
}

# Criar script de desinstalação
create_uninstall_script() {
    log "Criando script de desinstalação..."

    cat > "$PROJECT_DIR/uninstall_ragpp_cron.sh" << 'EOF'
#!/bin/bash
# RAG++ Cron Jobs Uninstaller
# Remove os cron jobs instalados automaticamente

set -e

echo "🗑️  Removendo cron jobs RAG++..."

# Fazer backup antes de remover
crontab -l > "crontab_backup_uninstall_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true

# Remover jobs RAG++
crontab -l 2>/dev/null | grep -v "RAG++" | grep -v "ragpp" | crontab -

echo "✅ Cron jobs RAG++ removidos"
echo "💡 Backup salvo como: crontab_backup_uninstall_*"
EOF

    chmod +x "$PROJECT_DIR/uninstall_ragpp_cron.sh"

    log "✅ Script de desinstalação criado: uninstall_ragpp_cron.sh"
}

# Mostrar instruções de uso
show_instructions() {
    echo ""
    log "🎉 Instalação concluída!"
    echo ""
    echo "📋 Próximos passos:"
    echo "   1. Verifique os cron jobs: crontab -l"
    echo "   2. Teste a manutenção: ./maintenance_ragpp.sh"
    echo "   3. Monitore os logs: tail -f /var/log/ragpp_maintenance.log"
    echo ""
    echo "🛠️  Comandos úteis:"
    echo "   • Editar cron jobs: crontab -e"
    echo "   • Desinstalar: ./uninstall_ragpp_cron.sh"
    echo "   • Ver status: systemctl list-timers"
    echo ""
    echo "📊 Cron jobs ativos:"
    echo "   • Manutenção semanal (domingo 2:00 AM)"
    echo "   • Backup diário (3:00 AM)"
    echo "   • Monitoramento (a cada 30 min)"
    echo "   • Limpeza de logs (segunda 4:00 AM)"
    echo "   • Verificação de integridade (6:00 AM)"
    echo "   • Reinício preventivo (mês 1, 5:00 AM)"
    echo "   • Atualização de dependências (mês 15, 2:00 AM)"
}

# Função principal
main() {
    echo "⏰ RAG++ Cron Jobs Installer"
    echo "==========================="

    check_config
    backup_crontab
    install_cron_jobs
    verify_installation
    create_uninstall_script
    show_instructions
}

# Executar apenas se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi