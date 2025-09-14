#!/bin/bash
# RAG++ Remote Server Startup Script

echo "🌐 Iniciando RAG++ para Acesso Remoto"
echo "===================================="

# Configurar variáveis de ambiente
export RAG_API_TOKEN="wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo"
export RAG_HOST="0.0.0.0"  # Escuta em todas as interfaces
export RAG_PORT="8000"

# IPs detectados
echo "🔍 Informações de Rede:"
echo "  IP Local: 172.20.7.45"
echo "  IP Público: 179.125.169.148"
echo ""

# Verificar se a porta está livre
if lsof -i :8000 &> /dev/null; then
    echo "⚠️  Porta 8000 já está em uso!"
    echo "Parando processos existentes..."
    pkill -f "ragpp_web_server"
    sleep 2
fi

# Iniciar servidor
echo "🚀 Iniciando servidor RAG++..."
echo "📱 Acesso Local: http://172.20.7.45:8000"
if [ "179.125.169.148" != "None" ] && [ "179.125.169.148" != "" ]; then
    echo "🌐 Acesso Remoto: http://179.125.169.148:8000"
fi
echo "📖 Documentação: http://172.20.7.45:8000/docs"
echo ""
echo "⏹️  Para parar: Ctrl+C ou 'pkill -f ragpp_web_server'"
echo ""

# Executar servidor
cd /home/agourakis82/workspace/pcs-meta-repo
python ragpp/ragpp_web_server.py

echo "🛑 Servidor parado."
