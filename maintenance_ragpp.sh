#!/bin/bash
# RAG++ Maintenance Script
# Executa manutenção automática do sistema RAG++

set -e

# Configurações
PROJECT_DIR="/home/agourakis82/workspace/pcs-meta-repo"
LOG_FILE="/var/log/ragpp_maintenance.log"
MAINTENANCE_INTERVAL=7  # dias

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

# Verificar se deve executar manutenção
should_run_maintenance() {
    local last_run_file="$PROJECT_DIR/.last_maintenance"

    if [ ! -f "$last_run_file" ]; then
        return 0  # Nunca executou
    fi

    local last_run=$(cat "$last_run_file")
    local now=$(date +%s)
    local diff=$(( (now - last_run) / 86400 ))  # diferença em dias

    if [ $diff -ge $MAINTENANCE_INTERVAL ]; then
        return 0  # Deve executar
    else
        return 1  # Ainda não é hora
    fi
}

# Atualizar timestamp da última manutenção
update_last_run() {
    date +%s > "$PROJECT_DIR/.last_maintenance"
}

# Verificar saúde do sistema
check_system_health() {
    log "Verificando saúde do sistema..."

    # Verificar espaço em disco
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $disk_usage -gt 90 ]; then
        error "Espaço em disco crítico: ${disk_usage}% usado"
        return 1
    elif [ $disk_usage -gt 80 ]; then
        warn "Espaço em disco alto: ${disk_usage}% usado"
    fi

    # Verificar memória
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ $mem_usage -gt 90 ]; then
        error "Uso de memória crítico: ${mem_usage}% usado"
        return 1
    fi

    # Verificar conectividade do servidor
    if ! curl -s --max-time 10 "http://localhost:8000/health" > /dev/null; then
        warn "Servidor RAG++ não responde"
    else
        info "Servidor RAG++ está saudável"
    fi

    log "✅ Verificação de saúde concluída"
}

# Limpar cache antigo
clean_old_cache() {
    log "Limpando cache antigo..."

    # Cache do sistema RAG++
    local cache_dir="$PROJECT_DIR/ragpp/cache"
    if [ -d "$cache_dir" ]; then
        # Remover arquivos de cache com mais de 30 dias
        find "$cache_dir" -type f -mtime +30 -delete 2>/dev/null || true
        info "Cache antigo limpo"
    fi

    # Cache do sistema
    if command -v systemd-tmpfiles &> /dev/null; then
        sudo systemd-tmpfiles --clean 2>/dev/null || true
    fi

    log "✅ Limpeza de cache concluída"
}

# Otimizar banco de dados
optimize_database() {
    log "Otimizando banco de dados..."

    local db_dir="$PROJECT_DIR/ragpp/index"
    if [ -d "$db_dir" ]; then
        # Verificar se há arquivos de lock antigos
        find "$db_dir" -name "*.lock" -mtime +1 -delete 2>/dev/null || true

        # Compactar arquivos de log se existirem
        find "$db_dir" -name "*.log" -mtime +7 -exec gzip {} \; 2>/dev/null || true

        info "Banco de dados otimizado"
    else
        warn "Diretório do banco não encontrado: $db_dir"
    fi

    log "✅ Otimização de banco concluída"
}

# Limpar logs antigos
clean_old_logs() {
    log "Limpando logs antigos..."

    # Logs do sistema
    if [ -f "$LOG_FILE" ]; then
        # Manter apenas últimas 1000 linhas
        tail -1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
    fi

    # Logs do systemd
    if command -v journalctl &> /dev/null; then
        sudo journalctl --vacuum-time=7d 2>/dev/null || true
    fi

    # Arquivos de log no projeto
    find "$PROJECT_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null || true

    log "✅ Limpeza de logs concluída"
}

# Executar backup automático
run_automatic_backup() {
    log "Executando backup automático..."

    local backup_script="$PROJECT_DIR/backup_ragpp.sh"
    if [ -f "$backup_script" ]; then
        bash "$backup_script"
        info "Backup automático executado"
    else
        warn "Script de backup não encontrado: $backup_script"
    fi

    log "✅ Backup automático concluído"
}

# Verificar e reiniciar serviços se necessário
check_services() {
    log "Verificando serviços..."

    # Verificar serviço ragpp
    if ! systemctl is-active --quiet ragpp 2>/dev/null; then
        warn "Serviço ragpp não está ativo, tentando reiniciar..."
        sudo systemctl restart ragpp 2>/dev/null || error "Falha ao reiniciar serviço ragpp"
    else
        info "Serviço ragpp está ativo"
    fi

    log "✅ Verificação de serviços concluída"
}

# Gerar relatório de manutenção
generate_report() {
    log "Gerando relatório de manutenção..."

    local report_file="$PROJECT_DIR/reports/maintenance_$(date +%Y%m%d).md"

    mkdir -p "$PROJECT_DIR/reports"

    cat > "$report_file" << EOF
# Relatório de Manutenção RAG++
Data: $(date '+%Y-%m-%d %H:%M:%S')

## Status do Sistema
- Espaço em disco: $(df -h / | tail -1 | awk '{print $5}')
- Uso de memória: $(free -h | grep Mem | awk '{print $3 "/" $2}')
- Carga do sistema: $(uptime | awk -F'load average:' '{print $2}')

## Ações Executadas
- ✅ Verificação de saúde do sistema
- ✅ Limpeza de cache antigo
- ✅ Otimização de banco de dados
- ✅ Limpeza de logs antigos
- ✅ Backup automático
- ✅ Verificação de serviços

## Backups Recentes
$(ls -la $PROJECT_DIR/backups/*.tar.gz 2>/dev/null | head -5 || echo "Nenhum backup encontrado")

## Próxima Manutenção
Agendada para: $(date -d "+${MAINTENANCE_INTERVAL} days" '+%Y-%m-%d')

---
*Relatório gerado automaticamente pelo sistema de manutenção RAG++*
EOF

    log "✅ Relatório gerado: $report_file"
}

# Enviar notificação (opcional)
send_notification() {
    local subject="RAG++ Maintenance Report - $(date '+%Y-%m-%d')"
    local body="Manutenção automática concluída com sucesso. Verifique o relatório em $PROJECT_DIR/reports/"

    # Se o mail estiver disponível
    if command -v mail &> /dev/null && [ -n "$ADMIN_EMAIL" ]; then
        echo "$body" | mail -s "$subject" "$ADMIN_EMAIL" 2>/dev/null || true
    fi
}

# Função principal
main() {
    echo "🔧 RAG++ Maintenance System"
    echo "=========================="

    # Verificar se deve executar
    if ! should_run_maintenance; then
        info "Manutenção não necessária ainda (última execução: $(date -d "@$(cat $PROJECT_DIR/.last_maintenance 2>/dev/null || echo 0)" '+%Y-%m-%d %H:%M:%S'))"
        exit 0
    fi

    log "Iniciando manutenção automática..."

    # Executar tarefas de manutenção
    check_system_health
    clean_old_cache
    optimize_database
    clean_old_logs
    run_automatic_backup
    check_services
    generate_report

    # Atualizar timestamp
    update_last_run

    # Enviar notificação
    send_notification

    echo ""
    log "🎉 Manutenção concluída com sucesso!"
    echo ""
    echo "📊 Resumo:"
    echo "   • Saúde do sistema verificada"
    echo "   • Cache e logs limpos"
    echo "   • Banco de dados otimizado"
    echo "   • Backup automático executado"
    echo "   • Serviços verificados"
    echo "   • Relatório gerado"
}

# Executar apenas se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi