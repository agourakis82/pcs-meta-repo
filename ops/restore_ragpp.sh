#!/bin/bash
# RAG++ Restore Script
# Restaura dados do backup do sistema RAG++

set -e

# Configurações
PROJECT_DIR="/home/agourakis82/workspace/pcs-meta-repo"
BACKUP_DIR="/home/agourakis82/workspace/pcs-meta-repo/backups"

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

# Verificar se arquivo de backup existe
check_backup_file() {
    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        error "Arquivo de backup não encontrado: $backup_file"
        exit 1
    fi

    if [[ ! "$backup_file" =~ \.tar\.gz$ ]]; then
        error "Arquivo deve ter extensão .tar.gz"
        exit 1
    fi

    log "✅ Arquivo de backup válido: $backup_file"
}

# Extrair backup
extract_backup() {
    local backup_file="$1"
    local temp_dir="/tmp/ragpp_restore_$(date +%s)"

    log "Extraindo backup..."

    mkdir -p "$temp_dir"
    tar -xzf "$backup_file" -C "$temp_dir"

    # Encontrar diretório extraído
    local extracted_dir=$(find "$temp_dir" -mindepth 1 -maxdepth 1 -type d | head -1)

    if [ -z "$extracted_dir" ]; then
        error "Não foi possível encontrar diretório extraído"
        rm -rf "$temp_dir"
        exit 1
    fi

    echo "$extracted_dir"
}

# Mostrar informações do backup
show_backup_info() {
    local backup_dir="$1"
    local metadata_file="$backup_dir/backup_metadata.json"

    if [ -f "$metadata_file" ]; then
        info "📊 Informações do backup:"
        echo "   Nome: $(jq -r '.backup_name' "$metadata_file" 2>/dev/null || echo 'N/A')"
        echo "   Criado em: $(jq -r '.created_at' "$metadata_file" 2>/dev/null || echo 'N/A')"
        echo "   Status do servidor: $(jq -r '.server_status' "$metadata_file" 2>/dev/null || echo 'N/A')"
        echo ""
    fi
}

# Confirmar restauração
confirm_restore() {
    local backup_dir="$1"

    echo "⚠️  ATENÇÃO: Esta operação irá sobrescrever dados existentes!"
    echo ""
    echo "📁 Diretórios que serão afetados:"
    echo "   • $PROJECT_DIR/ragpp/index/ (banco RAG)"
    echo "   • Configurações do sistema"
    echo ""
    echo "💾 Backup a ser restaurado: $backup_dir"

    read -p "Deseja continuar? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Restauração cancelada pelo usuário"
        exit 0
    fi
}

# Parar serviços antes da restauração
stop_services() {
    log "Parando serviços..."

    # Parar serviço systemd
    if systemctl is-active --quiet ragpp 2>/dev/null; then
        sudo systemctl stop ragpp
        log "✅ Serviço ragpp parado"
    fi

    # Aguardar um pouco
    sleep 2
}

# Restaurar banco RAG
restore_rag_database() {
    local backup_dir="$1"
    local rag_backup="$backup_dir/rag_db"

    if [ -d "$rag_backup" ]; then
        log "Restaurando banco RAG..."

        # Criar backup do banco atual
        local current_db="$PROJECT_DIR/ragpp/index"
        if [ -d "$current_db" ]; then
            local backup_current="$current_db.backup_$(date +%s)"
            mv "$current_db" "$backup_current"
            warn "Banco atual movido para: $backup_current"
        fi

        # Restaurar banco
        mkdir -p "$PROJECT_DIR/ragpp"
        cp -r "$rag_backup" "$PROJECT_DIR/ragpp/index"

        log "✅ Banco RAG restaurado"
    else
        warn "Backup do banco RAG não encontrado"
    fi
}

# Restaurar configurações
restore_configurations() {
    local backup_dir="$1"
    local config_backup="$backup_dir/config"

    if [ -d "$config_backup" ]; then
        log "Restaurando configurações..."

        # Arquivos de configuração a restaurar
        local config_files=(
            "ragpp.service"
            "setup_production.sh"
            "monitor_ragpp.sh"
            ".env"
            "environment.yml"
            "CITATION.cff"
            "metadata.yaml"
        )

        for file in "${config_files[@]}"; do
            if [ -f "$config_backup/$file" ]; then
                # Criar backup do arquivo atual
                if [ -f "$PROJECT_DIR/$file" ]; then
                    cp "$PROJECT_DIR/$file" "$PROJECT_DIR/$file.backup"
                fi

                # Restaurar arquivo
                cp "$config_backup/$file" "$PROJECT_DIR/$file"
                info "   • $file restaurado"
            fi
        done

        log "✅ Configurações restauradas"
    else
        warn "Backup de configurações não encontrado"
    fi
}

# Reiniciar serviços
restart_services() {
    log "Reiniciando serviços..."

    # Recarregar systemd se necessário
    if [ -f "$PROJECT_DIR/ragpp.service" ]; then
        sudo cp "$PROJECT_DIR/ragpp.service" /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable ragpp
        sudo systemctl start ragpp

        # Aguardar inicialização
        sleep 5

        # Verificar status
        if systemctl is-active --quiet ragpp; then
            log "✅ Serviço ragpp reiniciado com sucesso"
        else
            warn "Serviço ragpp não iniciou corretamente"
        fi
    fi
}

# Limpar arquivos temporários
cleanup() {
    local temp_dir="$1"

    if [ -d "$temp_dir" ]; then
        rm -rf "$temp_dir"
        log "✅ Arquivos temporários limpos"
    fi
}

# Função principal
main() {
    echo "🔄 RAG++ Restore System"
    echo "======================"

    if [ $# -eq 0 ]; then
        echo "Uso: $0 <arquivo_backup.tar.gz>"
        echo ""
        echo "Backups disponíveis:"
        if [ -d "$BACKUP_DIR" ]; then
            ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -10
        fi
        exit 1
    fi

    local backup_file="$1"

    # Verificar backup
    check_backup_file "$backup_file"

    # Extrair backup
    local temp_dir
    temp_dir=$(extract_backup "$backup_file")

    # Mostrar informações
    show_backup_info "$temp_dir"

    # Confirmar
    confirm_restore "$backup_file"

    # Executar restauração
    stop_services
    restore_rag_database "$temp_dir"
    restore_configurations "$temp_dir"
    restart_services

    # Limpar
    cleanup "$temp_dir"

    echo ""
    log "🎉 Restauração concluída com sucesso!"
    echo ""
    echo "📋 Verificações recomendadas:"
    echo "   • Verificar status do serviço: systemctl status ragpp"
    echo "   • Testar conectividade: curl http://localhost:8000/health"
    echo "   • Verificar logs: journalctl -u ragpp -f"
}

# Executar apenas se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi