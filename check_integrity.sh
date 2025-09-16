#!/bin/bash
# RAG++ Integrity Check Script
# Verifica a integridade dos componentes do sistema RAG++

set -e

# Configurações
PROJECT_DIR="/home/agourakis82/workspace/pcs-meta-repo"
REPORT_FILE="$PROJECT_DIR/reports/integrity_check_$(date +%Y%m%d_%H%M%S).md"

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

# Inicializar relatório
init_report() {
    mkdir -p "$PROJECT_DIR/reports"

    cat > "$REPORT_FILE" << EOF
# Relatório de Verificação de Integridade RAG++
Data: $(date '+%Y-%m-%d %H:%M:%S')
Status: Em andamento

## Componentes Verificados
EOF
}

# Atualizar relatório
update_report() {
    local component="$1"
    local status="$2"
    local details="$3"

    echo "- **$component**: $status" >> "$REPORT_FILE"
    if [ -n "$details" ]; then
        echo "  - $details" >> "$REPORT_FILE"
    fi
}

# Verificar arquivos essenciais
check_essential_files() {
    log "Verificando arquivos essenciais..."

    local essential_files=(
        "ragpp_server_optimized.py"
        "ragpp/cache_manager.py"
        "ragpp.service"
        "setup_production.sh"
        "monitor_ragpp.sh"
        "backup_ragpp.sh"
        "maintenance_ragpp.sh"
    )

    local missing_files=()

    for file in "${essential_files[@]}"; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            update_report "$file" "✅ Presente" ""
        else
            missing_files+=("$file")
            update_report "$file" "❌ Ausente" ""
        fi
    done

    if [ ${#missing_files[@]} -gt 0 ]; then
        warn "Arquivos essenciais ausentes: ${missing_files[*]}"
    else
        log "✅ Todos os arquivos essenciais estão presentes"
    fi
}

# Verificar permissões dos arquivos
check_file_permissions() {
    log "Verificando permissões dos arquivos..."

    local issues=0

    # Scripts devem ser executáveis
    local scripts=(
        "setup_production.sh"
        "monitor_ragpp.sh"
        "backup_ragpp.sh"
        "maintenance_ragpp.sh"
        "install_ragpp_cron.sh"
    )

    for script in "${scripts[@]}"; do
        if [ -f "$PROJECT_DIR/$script" ]; then
            if [ ! -x "$PROJECT_DIR/$script" ]; then
                warn "Script não executável: $script"
                update_report "Permissões - $script" "⚠️  Não executável" "Executar: chmod +x $script"
                ((issues++))
            else
                update_report "Permissões - $script" "✅ OK" ""
            fi
        fi
    done

    if [ $issues -eq 0 ]; then
        log "✅ Permissões dos arquivos estão corretas"
    fi
}

# Verificar serviço systemd
check_systemd_service() {
    log "Verificando serviço systemd..."

    if systemctl is-active --quiet ragpp 2>/dev/null; then
        update_report "Serviço Systemd" "✅ Ativo" ""
        log "✅ Serviço ragpp está ativo"
    elif systemctl is-enabled --quiet ragpp 2>/dev/null; then
        update_report "Serviço Systemd" "⚠️  Habilitado mas parado" "Executar: sudo systemctl start ragpp"
        warn "Serviço ragpp está habilitado mas parado"
    else
        update_report "Serviço Systemd" "❌ Não instalado" "Executar: sudo ./setup_production.sh"
        error "Serviço ragpp não está instalado"
    fi
}

# Verificar conectividade do servidor
check_server_connectivity() {
    log "Verificando conectividade do servidor..."

    if curl -s --max-time 5 "http://localhost:8000/health" > /dev/null; then
        update_report "Conectividade do Servidor" "✅ OK" ""
        log "✅ Servidor está respondendo"
    else
        update_report "Conectividade do Servidor" "❌ Indisponível" "Verificar logs: journalctl -u ragpp -f"
        error "Servidor não está respondendo"
    fi
}

# Verificar banco de dados
check_database() {
    log "Verificando banco de dados..."

    local db_dir="$PROJECT_DIR/ragpp/index"

    if [ -d "$db_dir" ]; then
        local db_size=$(du -sh "$db_dir" | cut -f1)
        local file_count=$(find "$db_dir" -type f | wc -l)

        update_report "Banco de Dados" "✅ Presente" "Tamanho: $db_size, Arquivos: $file_count"
        log "✅ Banco de dados encontrado: $db_size, $file_count arquivos"
    else
        update_report "Banco de Dados" "❌ Não encontrado" "Diretório: $db_dir"
        error "Banco de dados não encontrado"
    fi
}

# Verificar espaço em disco
check_disk_space() {
    log "Verificando espaço em disco..."

    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    local available=$(df -h / | tail -1 | awk '{print $4}')

    if [ $disk_usage -gt 90 ]; then
        update_report "Espaço em Disco" "❌ Crítico" "${disk_usage}% usado, disponível: $available"
        error "Espaço em disco crítico: ${disk_usage}% usado"
    elif [ $disk_usage -gt 80 ]; then
        update_report "Espaço em Disco" "⚠️  Alto" "${disk_usage}% usado, disponível: $available"
        warn "Espaço em disco alto: ${disk_usage}% usado"
    else
        update_report "Espaço em Disco" "✅ OK" "${disk_usage}% usado, disponível: $available"
        log "✅ Espaço em disco adequado"
    fi
}

# Verificar backups
check_backups() {
    log "Verificando backups..."

    local backup_dir="$PROJECT_DIR/backups"

    if [ -d "$backup_dir" ]; then
        local backup_count=$(ls -1 "$backup_dir"/*.tar.gz 2>/dev/null | wc -l)
        local latest_backup=$(ls -t "$backup_dir"/*.tar.gz 2>/dev/null | head -1)

        if [ $backup_count -gt 0 ]; then
            local latest_date=$(stat -c %y "$latest_backup" | cut -d' ' -f1)
            update_report "Backups" "✅ Presentes" "$backup_count backups, último: $latest_date"
            log "✅ $backup_count backups encontrados, último: $latest_date"
        else
            update_report "Backups" "⚠️  Nenhum backup" "Executar: ./backup_ragpp.sh"
            warn "Nenhum backup encontrado"
        fi
    else
        update_report "Backups" "❌ Diretório não existe" "Diretório: $backup_dir"
        error "Diretório de backups não existe"
    fi
}

# Verificar cron jobs
check_cron_jobs() {
    log "Verificando cron jobs..."

    local cron_count=$(crontab -l 2>/dev/null | grep -c "ragpp" || echo "0")

    if [ "$cron_count" -gt 0 ]; then
        update_report "Cron Jobs" "✅ Instalados" "$cron_count jobs ativos"
        log "✅ $cron_count cron jobs instalados"
    else
        update_report "Cron Jobs" "⚠️  Não instalados" "Executar: ./install_ragpp_cron.sh"
        warn "Nenhum cron job instalado"
    fi
}

# Finalizar relatório
finalize_report() {
    log "Finalizando relatório..."

    # Contar problemas
    local critical_issues=$(grep -c "❌" "$REPORT_FILE" || echo "0")
    local warnings=$(grep -c "⚠️" "$REPORT_FILE" || echo "0")

    # Atualizar status
    if [ $critical_issues -gt 0 ]; then
        sed -i 's/Status: Em andamento/Status: PROBLEMAS CRÍTICOS DETECTADOS/' "$REPORT_FILE"
    elif [ $warnings -gt 0 ]; then
        sed -i 's/Status: Em andamento/Status: ATENÇÃO NECESSÁRIA/' "$REPORT_FILE"
    else
        sed -i 's/Status: Em andamento/Status: SISTEMA SAUDÁVEL/' "$REPORT_FILE"
    fi

    # Adicionar resumo
    cat >> "$REPORT_FILE" << EOF

## Resumo
- Problemas críticos: $critical_issues
- Avisos: $warnings
- Verificado em: $(date '+%Y-%m-%d %H:%M:%S')

## Recomendações
EOF

    if [ $critical_issues -gt 0 ]; then
        echo "- Corrigir problemas críticos imediatamente" >> "$REPORT_FILE"
    fi

    if [ $warnings -gt 0 ]; then
        echo "- Revisar avisos e aplicar correções quando possível" >> "$REPORT_FILE"
    fi

    echo "- Executar verificações regularmente" >> "$REPORT_FILE"

    log "✅ Relatório finalizado: $REPORT_FILE"
}

# Função principal
main() {
    echo "🔍 RAG++ Integrity Check"
    echo "======================="

    init_report

    log "Iniciando verificação de integridade..."

    check_essential_files
    check_file_permissions
    check_systemd_service
    check_server_connectivity
    check_database
    check_disk_space
    check_backups
    check_cron_jobs

    finalize_report

    echo ""
    log "🎉 Verificação concluída!"
    echo ""
    echo "📊 Relatório salvo em: $REPORT_FILE"
    echo ""
    echo "📋 Resumo:"
    echo "   • Arquivos essenciais verificados"
    echo "   • Permissões dos arquivos checadas"
    echo "   • Serviço systemd validado"
    echo "   • Conectividade do servidor testada"
    echo "   • Banco de dados analisado"
    echo "   • Espaço em disco monitorado"
    echo "   • Backups verificados"
    echo "   • Cron jobs confirmados"
}

# Executar apenas se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi