#!/bin/bash
# RAG++ Backup Script
# Faz backup dos dados importantes do sistema RAG++

set -e

# Configurações
PROJECT_DIR="/home/agourakis82/workspace/pcs-meta-repo"
BACKUP_DIR="/home/agourakis82/workspace/pcs-meta-repo/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ragpp_backup_$DATE"
FULL_BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Criar diretório de backup
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log "✅ Diretório de backup criado: $BACKUP_DIR"
    fi
}

# Backup do banco de dados RAG
backup_rag_database() {
    log "Fazendo backup do banco RAG..."

    RAG_DB_DIR="$PROJECT_DIR/ragpp/index"
    if [ -d "$RAG_DB_DIR" ]; then
        mkdir -p "$FULL_BACKUP_PATH/rag_db"
        cp -r "$RAG_DB_DIR"/* "$FULL_BACKUP_PATH/rag_db/" 2>/dev/null || true
        log "✅ Banco RAG backup feito"
    else
        warn "Diretório do banco RAG não encontrado: $RAG_DB_DIR"
    fi
}

# Backup dos dados de memória
backup_memory_data() {
    log "Fazendo backup dos dados de memória..."

    # Tentar fazer dump via API se o servidor estiver rodando
    if curl -s --max-time 5 "http://localhost:8000/health" > /dev/null; then
        log "Servidor ativo, fazendo dump via API..."

        # Memory stats
        curl -s "http://localhost:8000/memory/stats" > "$FULL_BACKUP_PATH/memory_stats.json" 2>/dev/null || true

        # Recent memories
        curl -s "http://localhost:8000/memory/recent" > "$FULL_BACKUP_PATH/recent_memories.json" 2>/dev/null || true

        log "✅ Dados de memória backup via API"
    else
        warn "Servidor não ativo, pulando backup via API"
    fi
}

# Backup de configurações
backup_configurations() {
    log "Fazendo backup das configurações..."

    # Arquivos de configuração
    CONFIG_FILES=(
        "ragpp.service"
        "setup_production.sh"
        "monitor_ragpp.sh"
        ".env"
        "environment.yml"
        "CITATION.cff"
        "metadata.yaml"
    )

    mkdir -p "$FULL_BACKUP_PATH/config"

    for file in "${CONFIG_FILES[@]}"; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            cp "$PROJECT_DIR/$file" "$FULL_BACKUP_PATH/config/"
        fi
    done

    log "✅ Configurações backup feitas"
}

# Backup de logs
backup_logs() {
    log "Fazendo backup dos logs..."

    mkdir -p "$FULL_BACKUP_PATH/logs"

    # Systemd logs
    journalctl -u ragpp --since "7 days ago" > "$FULL_BACKUP_PATH/logs/systemd_ragpp.log" 2>/dev/null || true

    # Arquivos de log locais
    if [ -f "/var/log/ragpp_monitor.log" ]; then
        cp "/var/log/ragpp_monitor.log" "$FULL_BACKUP_PATH/logs/"
    fi

    log "✅ Logs backup feitos"
}

# Criar arquivo de metadados do backup
create_metadata() {
    log "Criando metadados do backup..."

    cat > "$FULL_BACKUP_PATH/backup_metadata.json" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "created_at": "$(date -Iseconds)",
    "project_dir": "$PROJECT_DIR",
    "server_status": "$(curl -s --max-time 5 http://localhost:8000/health | grep -q healthy && echo 'online' || echo 'offline')",
    "system_info": {
        "hostname": "$(hostname)",
        "kernel": "$(uname -r)",
        "architecture": "$(uname -m)"
    },
    "contents": {
        "rag_database": $([ -d "$FULL_BACKUP_PATH/rag_db" ] && echo "true" || echo "false"),
        "memory_data": $([ -f "$FULL_BACKUP_PATH/memory_stats.json" ] && echo "true" || echo "false"),
        "configurations": $([ -d "$FULL_BACKUP_PATH/config" ] && echo "true" || echo "false"),
        "logs": $([ -d "$FULL_BACKUP_PATH/logs" ] && echo "true" || echo "false")
    }
}
EOF

    log "✅ Metadados criados"
}

# Comprimir backup
compress_backup() {
    log "Comprimindo backup..."

    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"

    # Calcular tamanho
    SIZE=$(du -sh "${BACKUP_NAME}.tar.gz" | cut -f1)

    # Remover diretório não comprimido
    rm -rf "$BACKUP_NAME"

    log "✅ Backup comprimido: ${BACKUP_NAME}.tar.gz (${SIZE})"
}

# Limpar backups antigos
cleanup_old_backups() {
    log "Limpando backups antigos..."

    # Manter apenas os últimos 10 backups
    cd "$BACKUP_DIR"
    ls -t *.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm

    log "✅ Backups antigos limpos"
}

# Função principal
main() {
    echo "💾 RAG++ Backup System"
    echo "======================"

    create_backup_dir

    log "Iniciando backup: $BACKUP_NAME"

    # Executar backups
    backup_rag_database
    backup_memory_data
    backup_configurations
    backup_logs
    create_metadata
    compress_backup
    cleanup_old_backups

    echo ""
    log "🎉 Backup concluído com sucesso!"
    echo "📁 Localização: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    echo ""
    echo "📊 Conteúdo do backup:"
    echo "   • Banco de dados RAG"
    echo "   • Dados de memória"
    echo "   • Configurações do sistema"
    echo "   • Logs do sistema"
    echo "   • Metadados do backup"
}

# Executar apenas se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi