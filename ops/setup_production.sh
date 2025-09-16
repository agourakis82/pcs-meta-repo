#!/bin/bash
# RAG++ Production Setup Script
# Configura o servidor RAG++ para produção com systemd

set -e

echo "🚀 Configurando RAG++ para Produção"
echo "===================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se está rodando como root
if [[ $EUID -eq 0 ]]; then
   error "Este script não deve ser executado como root"
   exit 1
fi

# Diretórios
PROJECT_DIR="/home/agourakis82/workspace/pcs-meta-repo"
SERVICE_FILE="$PROJECT_DIR/ragpp.service"
SYSTEMD_DIR="/etc/systemd/system"

# 1. Criar usuário do sistema
log "Criando usuário do sistema 'ragpp'..."
if ! id "ragpp" &>/dev/null; then
    sudo useradd --system --shell /bin/bash --home /home/ragpp --create-home ragpp
    log "✅ Usuário 'ragpp' criado"
else
    log "✅ Usuário 'ragpp' já existe"
fi

# 2. Configurar permissões
log "Configurando permissões..."
sudo chown -R ragpp:ragpp "$PROJECT_DIR"
sudo chmod -R 755 "$PROJECT_DIR"
log "✅ Permissões configuradas"

# 3. Criar ambiente virtual se não existir
if [ ! -d "$PROJECT_DIR/venv" ]; then
    log "Criando ambiente virtual..."
    python3 -m venv "$PROJECT_DIR/venv"
    log "✅ Ambiente virtual criado"
else
    log "✅ Ambiente virtual já existe"
fi

# 4. Instalar dependências
log "Instalando dependências..."
source "$PROJECT_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt" 2>/dev/null || warn "requirements.txt não encontrado, pulando..."

# Instalar dependências específicas de performance
pip install uvloop httptools 2>/dev/null || warn "Dependências de performance não disponíveis"

log "✅ Dependências instaladas"

# 5. Copiar arquivo de serviço
log "Instalando serviço systemd..."
sudo cp "$SERVICE_FILE" "$SYSTEMD_DIR/"
sudo chmod 644 "$SYSTEMD_DIR/ragpp.service"
log "✅ Serviço instalado"

# 6. Recarregar systemd
log "Recarregando systemd..."
sudo systemctl daemon-reload
log "✅ Systemd recarregado"

# 7. Configurar firewall
log "Configurando firewall..."
sudo ufw allow 8000/tcp || warn "UFW não disponível"
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT 2>/dev/null || warn "iptables falhou"
log "✅ Firewall configurado"

# 8. Iniciar serviço
log "Iniciando serviço RAG++..."
sudo systemctl enable ragpp
sudo systemctl start ragpp

# Aguardar um pouco
sleep 3

# Verificar status
if sudo systemctl is-active --quiet ragpp; then
    log "✅ Serviço RAG++ iniciado com sucesso!"
    echo ""
    echo "📊 Status do serviço:"
    sudo systemctl status ragpp --no-pager -l
    echo ""
    echo "🔗 URLs:"
    echo "   📖 API Docs: http://localhost:8000/docs"
    echo "   🔌 Health Check: http://localhost:8000/health"
    echo "   🧠 Memory API: http://localhost:8000/memory/"
    echo "   📈 Cache Stats: http://localhost:8000/cache/stats"
    echo ""
    echo "🛠️ Comandos úteis:"
    echo "   sudo systemctl status ragpp     # Ver status"
    echo "   sudo systemctl restart ragpp    # Reiniciar"
    echo "   sudo systemctl stop ragpp       # Parar"
    echo "   sudo journalctl -u ragpp -f     # Ver logs"
else
    error "❌ Falha ao iniciar serviço RAG++"
    echo "Verifique os logs com: sudo journalctl -u ragpp -n 50"
    exit 1
fi

echo ""
log "🎉 Configuração de produção concluída!"
echo "RAG++ está rodando em http://localhost:8000"