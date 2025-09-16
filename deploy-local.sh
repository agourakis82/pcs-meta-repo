#!/bin/bash
# Script para deployment local com Docker

set -e

echo "🐳 Iniciando deployment local da Darwin Platform"

# Configurações
IMAGE_NAME=${IMAGE_NAME:-darwin-platform}
CONTAINER_NAME=${CONTAINER_NAME:-darwin-app}
PORT=${PORT:-8000}

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale primeiro:"
    echo "https://docs.docker.com/get-docker/"
    exit 1
fi

# Parar container existente se estiver rodando
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo "🛑 Parando container existente..."
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
fi

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    cat > .env << EOF
PROJECT_ID=local-development
LOCATION=us-central1
BASE_URL=http://localhost:$PORT
API_KEYS=dev-key-1,dev-key-2,dev-key-3
DEBUG=true
CONTEXT_CACHE_ENABLED=true
RAG_ENGINE_ENABLED=false
VECTOR_SEARCH_ENABLED=false
MEMORY_STORAGE_DIR=/tmp/darwin-memory
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60
EOF
    echo "✅ Arquivo .env criado com configurações de desenvolvimento"
fi

# Build da imagem
echo "🔨 Construindo imagem Docker..."
docker build -t "$IMAGE_NAME" .

# Run do container
echo "🚀 Iniciando container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:8000" \
    --env-file .env \
    -v "$(pwd)/data:/tmp/darwin-memory" \
    --restart unless-stopped \
    "$IMAGE_NAME"

# Aguardar container ficar pronto
echo "⏳ Aguardando container ficar pronto..."
sleep 5

# Verificar se está rodando
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo ""
    echo "🎉 Darwin Platform está rodando!"
    echo "📍 URL: http://localhost:$PORT"
    echo "📚 Documentação: http://localhost:$PORT/docs"
    echo "❤️  Health check: http://localhost:$PORT/health"
    echo ""
    echo "🧪 Testando health check..."
    sleep 2
    if curl -s "http://localhost:$PORT/health" > /dev/null; then
        echo "✅ Health check passou!"
    else
        echo "⚠️  Health check falhou. Verificando logs..."
        docker logs "$CONTAINER_NAME" --tail 20
    fi
    echo ""
    echo "📋 Comandos úteis:"
    echo "  Ver logs: docker logs $CONTAINER_NAME -f"
    echo "  Parar: docker stop $CONTAINER_NAME"
    echo "  Remover: docker rm $CONTAINER_NAME"
    echo "  Shell: docker exec -it $CONTAINER_NAME bash"
else
    echo "❌ Falha ao iniciar o container"
    docker logs "$CONTAINER_NAME"
    exit 1
fi