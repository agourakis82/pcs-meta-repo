#!/bin/bash
# Script master de deployment para Darwin Platform

set -e

echo "🚀 Darwin Platform - Deployment Master Script"
echo "=============================================="
echo ""

# Função para mostrar o menu
show_menu() {
    echo "Escolha o tipo de deployment:"
    echo ""
    echo "1) 🐳 Local (Docker)"
    echo "2) ☁️  Google Cloud Run"
    echo "3) 🚂 Railway"
    echo "4) ⚡ Desenvolvimento (Python direto)"
    echo "5) 🧪 Testes"
    echo "6) ❌ Sair"
    echo ""
}

# Função para deployment local
deploy_local() {
    echo "🐳 Deployment Local com Docker"
    echo "==============================="
    ./deploy-local.sh
}

# Função para deployment no GCP
deploy_gcp() {
    echo "☁️  Deployment no Google Cloud Run"
    echo "==================================="
    ./deploy-gcp.sh
}

# Função para deployment no Railway
deploy_railway() {
    echo "🚂 Deployment no Railway"
    echo "========================="
    ./deploy-railway.sh
}

# Função para desenvolvimento local
dev_local() {
    echo "⚡ Desenvolvimento Local"
    echo "========================"
    
    # Verificar se virtual environment existe
    if [ ! -d "venv" ]; then
        echo "📦 Criando virtual environment..."
        python3.11 -m venv venv
    fi
    
    # Ativar venv
    source venv/bin/activate
    
    # Instalar dependências
    echo "📥 Instalando dependências..."
    pip install -r requirements.txt
    pip install fastapi uvicorn pydantic pydantic-settings
    
    # Criar .env para desenvolvimento
    if [ ! -f .env ]; then
        cat > .env << 'EOF'
PROJECT_ID=local-development
LOCATION=us-central1
BASE_URL=http://localhost:8000
API_KEYS=dev-key-1,dev-key-2
DEBUG=true
CONTEXT_CACHE_ENABLED=true
RAG_ENGINE_ENABLED=false
VECTOR_SEARCH_ENABLED=false
MEMORY_STORAGE_DIR=/tmp/darwin-memory
EOF
        echo "✅ Arquivo .env criado"
    fi
    
    # Carregar variáveis
    export $(grep -v '^#' .env | xargs)
    
    echo "🚀 Iniciando servidor de desenvolvimento..."
    echo "📍 URL: http://localhost:8000"
    echo "📚 Docs: http://localhost:8000/docs"
    echo ""
    echo "Pressione Ctrl+C para parar"
    
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# Função para executar testes
run_tests() {
    echo "🧪 Executando Testes"
    echo "===================="
    
    if [ ! -d "venv" ]; then
        echo "📦 Criando virtual environment..."
        python3.11 -m venv venv
    fi
    
    source venv/bin/activate
    
    echo "📥 Instalando dependências de teste..."
    pip install -r requirements.txt
    pip install -r test-requirements.txt
    
    echo "🔬 Executando testes..."
    pytest tests/test_darwin_platform.py -v --tb=short
}

# Loop principal
while true; do
    show_menu
    read -p "Digite sua escolha (1-6): " choice
    echo ""
    
    case $choice in
        1)
            deploy_local
            ;;
        2)
            deploy_gcp
            ;;
        3)
            deploy_railway
            ;;
        4)
            dev_local
            ;;
        5)
            run_tests
            ;;
        6)
            echo "👋 Saindo..."
            exit 0
            ;;
        *)
            echo "❌ Opção inválida. Tente novamente."
            echo ""
            ;;
    esac
    
    echo ""
    echo "Pressione Enter para continuar..."
    read
    echo ""
done