#!/bin/bash
# Transfer RAG++ Extended Memory System to D: Drive
# Script para transferir todo o sistema RAG++ para o disco D:

echo "🚚 RAG++ System Transfer to D: Drive"
echo "===================================="

# Verificar se D: está acessível
if [ ! -d "/mnt/d" ]; then
    echo "❌ Error: D: drive not accessible at /mnt/d"
    exit 1
fi

echo "✅ D: drive accessible at /mnt/d"

# Definir caminhos
SOURCE_DIR="/home/agourakis82/workspace/pcs-meta-repo"
TARGET_BASE="/mnt/d/RAG_System"
TARGET_DIR="${TARGET_BASE}/pcs-meta-repo"
BACKUP_DIR="${TARGET_BASE}/backup_$(date +%Y%m%d_%H%M%S)"

echo "📂 Source: $SOURCE_DIR"
echo "📂 Target: $TARGET_DIR"
echo "💾 Backup: $BACKUP_DIR"

# Parar o serviço se estiver rodando
echo ""
echo "🛑 Stopping RAG++ Memory Service..."
cd "$SOURCE_DIR/ragpp" 2>/dev/null && ./manage_memory_service.sh stop 2>/dev/null || echo "Service not running"

# Criar estrutura de diretórios no D:
echo ""
echo "📁 Creating directory structure on D:..."
mkdir -p "$TARGET_BASE"
mkdir -p "$TARGET_DIR"
mkdir -p "$BACKUP_DIR"

# Função para transferir com progresso
transfer_with_progress() {
    local src="$1"
    local dst="$2"
    local desc="$3"
    
    echo "📦 Transferring $desc..."
    if [ -d "$src" ] || [ -f "$src" ]; then
        rsync -av --progress "$src" "$dst"
        echo "✅ $desc transferred successfully"
    else
        echo "⚠️  $desc not found, skipping..."
    fi
}

# 1. Transferir projeto principal
echo ""
echo "🔄 Phase 1: Main Project Transfer"
echo "================================="

# Core ragpp directory
transfer_with_progress "$SOURCE_DIR/ragpp/" "$TARGET_DIR/" "RAG++ Core System"

# Configuration files
transfer_with_progress "$SOURCE_DIR/README*.md" "$TARGET_DIR/" "Documentation"
transfer_with_progress "$SOURCE_DIR/requirements.txt" "$TARGET_DIR/" "Requirements"
transfer_with_progress "$SOURCE_DIR/pyproject.toml" "$TARGET_DIR/" "Python Project Config"
transfer_with_progress "$SOURCE_DIR/environment.yml" "$TARGET_DIR/" "Conda Environment"

# Scripts importantes
transfer_with_progress "$SOURCE_DIR/build_*.sh" "$TARGET_DIR/" "Build Scripts"
transfer_with_progress "$SOURCE_DIR/launch_*.sh" "$TARGET_DIR/" "Launch Scripts"
transfer_with_progress "$SOURCE_DIR/configure_*.sh" "$TARGET_DIR/" "Configuration Scripts"

# 2. Transferir dados específicos do projeto
echo ""
echo "🔄 Phase 2: Project Data Transfer"
echo "================================="

# Src directory (se existir)
if [ -d "$SOURCE_DIR/src" ]; then
    transfer_with_progress "$SOURCE_DIR/src/" "$TARGET_DIR/" "Source Code"
fi

# Config directory (se existir)
if [ -d "$SOURCE_DIR/config" ]; then
    transfer_with_progress "$SOURCE_DIR/config/" "$TARGET_DIR/" "Configuration Files"
fi

# Data directories importantes
for data_dir in data datasets outputs reports manuscripts; do
    if [ -d "$SOURCE_DIR/$data_dir" ]; then
        transfer_with_progress "$SOURCE_DIR/$data_dir/" "$TARGET_DIR/" "$data_dir Directory"
    fi
done

# 3. Backup dos dados de memória existentes
echo ""
echo "🔄 Phase 3: Memory Data Backup"
echo "=============================="

# Memory database
if [ -d "$SOURCE_DIR/ragpp/data" ]; then
    transfer_with_progress "$SOURCE_DIR/ragpp/data/" "$BACKUP_DIR/" "Memory Database Backup"
fi

# Logs
if [ -d "$SOURCE_DIR/ragpp/logs" ]; then
    transfer_with_progress "$SOURCE_DIR/ragpp/logs/" "$BACKUP_DIR/" "Service Logs Backup"
fi

# 4. Criar novos scripts de configuração para D:
echo ""
echo "🔄 Phase 4: Creating D: Drive Scripts"
echo "====================================="

# Script de inicialização para D:
cat > "$TARGET_DIR/start_ragpp_d_drive.sh" << 'EOF'
#!/bin/bash
# RAG++ Startup Script for D: Drive

echo "🚀 Starting RAG++ from D: Drive..."

# Set working directory
cd "/mnt/d/RAG_System/pcs-meta-repo/ragpp"

# Export paths
export RAGPP_DATA_DIR="/mnt/d/RAG_System/pcs-meta-repo/ragpp/data"
export RAGPP_LOGS_DIR="/mnt/d/RAG_System/pcs-meta-repo/ragpp/logs"

# Create directories if they don't exist
mkdir -p "$RAGPP_DATA_DIR"
mkdir -p "$RAGPP_LOGS_DIR"

# Start the service
echo "📍 Working from: $(pwd)"
echo "💾 Data directory: $RAGPP_DATA_DIR"
echo "📄 Logs directory: $RAGPP_LOGS_DIR"

./manage_memory_service.sh start
EOF

chmod +x "$TARGET_DIR/start_ragpp_d_drive.sh"

# Script de gerenciamento para D:
cat > "$TARGET_DIR/manage_ragpp_d_drive.sh" << 'EOF'
#!/bin/bash
# RAG++ Management Script for D: Drive

RAGPP_DIR="/mnt/d/RAG_System/pcs-meta-repo/ragpp"

case "${1:-status}" in
    start)
        echo "🚀 Starting RAG++ from D: Drive..."
        cd "$RAGPP_DIR"
        ./manage_memory_service.sh start
        ;;
    stop)
        echo "🛑 Stopping RAG++ service..."
        cd "$RAGPP_DIR"
        ./manage_memory_service.sh stop
        ;;
    restart)
        echo "🔄 Restarting RAG++ service..."
        cd "$RAGPP_DIR"
        ./manage_memory_service.sh restart
        ;;
    status)
        echo "📊 RAG++ Service Status:"
        cd "$RAGPP_DIR"
        ./manage_memory_service.sh status
        ;;
    logs)
        echo "📄 RAG++ Service Logs:"
        cd "$RAGPP_DIR"
        ./manage_memory_service.sh logs
        ;;
    cd)
        echo "📂 Use this command to go to RAG++ directory:"
        echo "cd $RAGPP_DIR"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|cd}"
        echo ""
        echo "RAG++ System Location: $RAGPP_DIR"
        ;;
esac
EOF

chmod +x "$TARGET_DIR/manage_ragpp_d_drive.sh"

# 5. Atualizar configurações para o novo local
echo ""
echo "🔄 Phase 5: Updating Configuration Files"
echo "======================================="

# Atualizar paths nos arquivos de configuração
if [ -f "$TARGET_DIR/ragpp/extended_memory_service.py" ]; then
    echo "🔧 Updating memory service paths..."
    sed -i 's|ragpp/data/memory|/mnt/d/RAG_System/pcs-meta-repo/ragpp/data/memory|g' "$TARGET_DIR/ragpp/extended_memory_service.py"
fi

# Atualizar script de gerenciamento
if [ -f "$TARGET_DIR/ragpp/manage_memory_service.sh" ]; then
    echo "🔧 Updating management script paths..."
    sed -i 's|/home/agourakis82/workspace/pcs-meta-repo/ragpp|/mnt/d/RAG_System/pcs-meta-repo/ragpp|g' "$TARGET_DIR/ragpp/manage_memory_service.sh"
fi

# 6. Atualizar serviços systemd
echo ""
echo "🔄 Phase 6: Updating Systemd Services"
echo "===================================="

# Backup do serviço atual
if [ -f "/home/agourakis82/.config/systemd/user/ragpp-memory-service.service" ]; then
    cp "/home/agourakis82/.config/systemd/user/ragpp-memory-service.service" "$BACKUP_DIR/"
    echo "💾 Systemd service backed up"
fi

# Criar novo serviço para D:
mkdir -p "/home/agourakis82/.config/systemd/user"
cat > "/home/agourakis82/.config/systemd/user/ragpp-memory-service.service" << EOF
[Unit]
Description=RAG++ Extended Memory Service (D: Drive)
After=network.target
Wants=network.target

[Service]
Type=simple
WorkingDirectory=/mnt/d/RAG_System/pcs-meta-repo/ragpp
Environment=HOME=/home/agourakis82
Environment=PATH=/usr/local/bin:/usr/bin:/bin:/home/agourakis82/.local/bin
Environment=RAGPP_DATA_DIR=/mnt/d/RAG_System/pcs-meta-repo/ragpp/data
ExecStart=/usr/bin/python3 /mnt/d/RAG_System/pcs-meta-repo/ragpp/memory_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

# Recarregar systemd
systemctl --user daemon-reload
systemctl --user enable ragpp-memory-service.service
echo "✅ Systemd service updated for D: drive"

# 7. Criar aliases úteis
echo ""
echo "🔄 Phase 7: Creating Convenient Aliases"
echo "======================================"

# Adicionar aliases ao .bashrc
ALIAS_CONTENT="
# RAG++ D: Drive Aliases
alias ragpp-cd='cd /mnt/d/RAG_System/pcs-meta-repo/ragpp'
alias ragpp-start='/mnt/d/RAG_System/pcs-meta-repo/manage_ragpp_d_drive.sh start'
alias ragpp-stop='/mnt/d/RAG_System/pcs-meta-repo/manage_ragpp_d_drive.sh stop'
alias ragpp-status='/mnt/d/RAG_System/pcs-meta-repo/manage_ragpp_d_drive.sh status'
alias ragpp-logs='/mnt/d/RAG_System/pcs-meta-repo/manage_ragpp_d_drive.sh logs'
alias ragpp-restart='/mnt/d/RAG_System/pcs-meta-repo/manage_ragpp_d_drive.sh restart'
"

if ! grep -q "RAG++ D: Drive Aliases" "/home/agourakis82/.bashrc"; then
    echo "$ALIAS_CONTENT" >> "/home/agourakis82/.bashrc"
    echo "✅ Aliases added to .bashrc"
else
    echo "⚠️  Aliases already exist in .bashrc"
fi

# 8. Verificar transferência
echo ""
echo "🔄 Phase 8: Verification"
echo "======================="

echo "📊 Disk usage comparison:"
echo "Original location:"
du -sh "$SOURCE_DIR" 2>/dev/null || echo "Source not accessible"

echo "New location:"
du -sh "$TARGET_DIR" 2>/dev/null || echo "Target not accessible"

echo ""
echo "📂 D: Drive contents:"
ls -la "$TARGET_BASE/"

# 9. Criar script de limpeza
echo ""
echo "🔄 Phase 9: Creating Cleanup Script"
echo "==================================="

cat > "$TARGET_DIR/cleanup_old_location.sh" << EOF
#!/bin/bash
# Script para limpar localização antiga após confirmação

echo "⚠️  WARNING: This will DELETE the original RAG++ installation!"
echo "📂 Original location: $SOURCE_DIR"
echo "📂 New location: $TARGET_DIR"
echo ""
echo "Make sure everything is working from D: drive before proceeding!"
echo ""
read -p "Are you sure you want to delete the original installation? (type 'DELETE' to confirm): " confirm

if [ "\$confirm" = "DELETE" ]; then
    echo "🗑️  Removing original installation..."
    rm -rf "$SOURCE_DIR/ragpp"
    echo "✅ Original ragpp directory removed"
    echo "💾 Backup available at: $BACKUP_DIR"
else
    echo "❌ Cleanup cancelled"
fi
EOF

chmod +x "$TARGET_DIR/cleanup_old_location.sh"

# 10. Resultado final
echo ""
echo "🎉 Transfer Complete!"
echo "===================="
echo ""
echo "✅ RAG++ System successfully transferred to D: drive!"
echo ""
echo "📂 New location: $TARGET_DIR"
echo "💾 Backup created: $BACKUP_DIR"
echo ""
echo "🚀 Quick start commands:"
echo "  cd /mnt/d/RAG_System/pcs-meta-repo/ragpp"
echo "  ./start_ragpp_d_drive.sh"
echo ""
echo "🔧 Management commands:"
echo "  ragpp-start    # Start service"
echo "  ragpp-stop     # Stop service"
echo "  ragpp-status   # Check status"
echo "  ragpp-logs     # View logs"
echo "  ragpp-cd       # Go to directory"
echo ""
echo "⚠️  Remember to:"
echo "1. Test the system from D: drive"
echo "2. Run cleanup script if everything works"
echo "3. Update any hardcoded paths in your configurations"
echo ""
echo "🎯 System is ready to start from D: drive!"
