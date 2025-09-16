#!/bin/bash
# Script para deployment no Railway

set -e

echo "🚂 Iniciando deployment da Darwin Platform no Railway"

# Verificar se Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI não encontrado. Instalando..."
    npm install -g @railway/cli
fi

# Verificar se está logado
if ! railway whoami &> /dev/null; then
    echo "🔑 Fazendo login no Railway..."
    railway login
fi

# Verificar se existe projeto
if ! railway status &> /dev/null; then
    echo "📦 Criando novo projeto Railway..."
    railway init
fi

# Configurar variáveis de ambiente
echo "⚙️  Configurando variáveis de ambiente..."

# Perguntar configurações básicas
read -p "Project ID do Google Cloud: " PROJECT_ID
read -p "Localização (us-central1): " LOCATION
LOCATION=${LOCATION:-us-central1}

# Configurar variáveis
railway variables set PROJECT_ID="$PROJECT_ID"
railway variables set LOCATION="$LOCATION"
railway variables set CONTEXT_CACHE_ENABLED=true
railway variables set RAG_ENGINE_ENABLED=true
railway variables set VECTOR_SEARCH_ENABLED=true
railway variables set MEMORY_STORAGE_DIR=/tmp/darwin-memory
railway variables set RATE_LIMIT_REQUESTS=100
railway variables set RATE_LIMIT_WINDOW=60
railway variables set DEBUG=false

# Perguntar por API keys
echo ""
echo "🔐 Configure suas API keys:"
read -p "API Keys (separadas por vírgula): " API_KEYS
if [ ! -z "$API_KEYS" ]; then
    railway variables set API_KEYS="$API_KEYS"
fi

read -p "OpenAI Verification Token (opcional): " OPENAI_TOKEN
if [ ! -z "$OPENAI_TOKEN" ]; then
    railway variables set OPENAI_VERIFICATION_TOKEN="$OPENAI_TOKEN"
fi

# Criar arquivo railway.toml se não existir
if [ ! -f railway.toml ]; then
    echo "📝 Criando railway.toml..."
    cat > railway.toml << 'EOF'
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on-failure"
restartPolicyMaxRetries = 3

[services.darwin-platform]
source = "."
EOF
fi

# Criar nixpacks.toml para configurar Python
if [ ! -f nixpacks.toml ]; then
    echo "📝 Criando nixpacks.toml..."
    cat > nixpacks.toml << 'EOF'
[phases.setup]
nixPkgs = ["python311", "gcc", "g++"]

[phases.install]
cmds = ["pip install -r requirements.txt", "pip install fastapi uvicorn pydantic pydantic-settings google-cloud-aiplatform google-cloud-secretmanager"]

[start]
cmd = "uvicorn main:app --host 0.0.0.0 --port $PORT"
EOF
fi

# Deploy
echo "🚀 Fazendo deployment..."
railway up --detach

# Aguardar deployment
echo "⏳ Aguardando deployment..."
sleep 10

# Obter URL do serviço
SERVICE_URL=$(railway domain)

if [ ! -z "$SERVICE_URL" ]; then
    echo ""
    echo "🎉 Deployment concluído com sucesso!"
    echo "📍 URL do serviço: https://$SERVICE_URL"
    echo "📚 Documentação da API: https://$SERVICE_URL/docs"
    echo "❤️  Health check: https://$SERVICE_URL/health"
    echo ""
    echo "🧪 Para testar:"
    echo "curl https://$SERVICE_URL/health"
    echo ""
    echo "📋 Comandos úteis:"
    echo "  Ver logs: railway logs"
    echo "  Status: railway status"
    echo "  Variáveis: railway variables"
else
    echo "⚠️  Deployment concluído, mas URL não encontrada"
    echo "📋 Verifique o status com: railway status"
fi