# 🚀 Guia de Deployment - Darwin Platform

Este guia ensina como fazer o deployment da plataforma Darwin em diferentes ambientes.

## 📋 Pré-requisitos

### 1. Configuração do Google Cloud

```bash
# 1.1 Instalar Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 1.2 Fazer login
gcloud auth login

# 1.3 Configurar projeto
gcloud config set project SEU-PROJECT-ID

# 1.4 Habilitar APIs necessárias
gcloud services enable aiplatform.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 1.2 Criar Service Account

```bash
# Criar service account
gcloud iam service-accounts create darwin-platform \
    --display-name="Darwin Platform Service Account"

# Dar permissões necessárias
gcloud projects add-iam-policy-binding SEU-PROJECT-ID \
    --member="serviceAccount:darwin-platform@SEU-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding SEU-PROJECT-ID \
    --member="serviceAccount:darwin-platform@SEU-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.accessor"

# Criar chave JSON (para desenvolvimento local)
gcloud iam service-accounts keys create darwin-key.json \
    --iam-account=darwin-platform@SEU-PROJECT-ID.iam.gserviceaccount.com
```

### 1.3 Configurar Secrets

```bash
# Criar secrets no Secret Manager
echo "your-api-key-1,your-api-key-2" | gcloud secrets create api-keys --data-file=-
echo "your-openai-verification-token" | gcloud secrets create openai-verification-token --data-file=-
```

## 🐳 Opção 1: Deployment com Docker Local

### 2.1 Criar Dockerfile

```dockerfile
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (para cache de layers)
COPY requirements.txt ./

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY services/ ./services/
COPY api/ ./api/
COPY main.py ./

# Criar diretório para dados temporários
RUN mkdir -p /tmp/darwin-memory

# Configurar usuário não-root
RUN useradd -m -u 1001 darwin
RUN chown -R darwin:darwin /app /tmp/darwin-memory
USER darwin

# Configurar variáveis de ambiente
ENV PYTHONPATH=/app
ENV MEMORY_STORAGE_DIR=/tmp/darwin-memory
ENV PORT=8000

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando para iniciar a aplicação
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 2.2 Build e Run Local

```bash
# Criar arquivo .env
cat > .env << EOF
PROJECT_ID=seu-project-id
LOCATION=us-central1
BASE_URL=http://localhost:8000
API_KEYS=test-key-1,test-key-2
DEBUG=true
CONTEXT_CACHE_ENABLED=true
RAG_ENGINE_ENABLED=true
VECTOR_SEARCH_ENABLED=true
EOF

# Build da imagem
docker build -t darwin-platform .

# Run local com variáveis de ambiente
docker run -p 8000:8000 --env-file .env darwin-platform

# Testar
curl http://localhost:8000/health
```

## ☁️ Opção 2: Google Cloud Run (Recomendado)

### 3.1 Configurar requirements.txt para produção

```bash
# Criar requirements-prod.txt
cat > requirements-prod.txt << EOF
# Darwin Platform Production Requirements
fastapi>=0.103.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
google-cloud-aiplatform>=1.36.0
google-cloud-secretmanager>=2.16.0
google-auth>=2.23.0
aiosqlite>=0.19.0
httpx>=0.24.0
aiofiles>=23.0.0
numpy>=1.24.0
asyncio-throttle>=1.0.2
python-multipart>=0.0.6
python-json-logger>=2.0.0
EOF
```

### 3.2 Deploy direto do código

```bash
# Deploy usando Cloud Build
gcloud run deploy darwin-platform \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars PROJECT_ID=$(gcloud config get-value project) \
    --set-env-vars LOCATION=us-central1 \
    --set-env-vars CONTEXT_CACHE_ENABLED=true \
    --set-env-vars RAG_ENGINE_ENABLED=true \
    --set-env-vars VECTOR_SEARCH_ENABLED=true \
    --service-account darwin-platform@$(gcloud config get-value project).iam.gserviceaccount.com
```

### 3.3 Deploy com Container Registry

```bash
# Build e push para Container Registry
gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/darwin-platform

# Deploy da imagem
gcloud run deploy darwin-platform \
    --image gcr.io/$(gcloud config get-value project)/darwin-platform \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars PROJECT_ID=$(gcloud config get-value project) \
    --set-env-vars LOCATION=us-central1 \
    --service-account darwin-platform@$(gcloud config get-value project).iam.gserviceaccount.com
```

## 🚂 Opção 3: Railway

### 4.1 Setup Railway

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Criar projeto
railway init

# Linkar ao repo
railway link
```

### 4.2 Configurar variáveis no Railway

```bash
# Configurar variáveis de ambiente
railway variables set PROJECT_ID=seu-project-id
railway variables set LOCATION=us-central1
railway variables set API_KEYS=key1,key2
railway variables set CONTEXT_CACHE_ENABLED=true
railway variables set RAG_ENGINE_ENABLED=true
railway variables set VECTOR_SEARCH_ENABLED=true

# Deploy
railway up
```

### 4.3 Arquivo railway.toml

```toml
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "on-failure"

[[services]]
name = "darwin-platform"

[services.volumes]
mountPath = "/tmp/darwin-memory"
```

## ⚡ Opção 4: Vercel (Para desenvolvimento)

### 5.1 Configurar Vercel

```bash
# Instalar Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel
```

### 5.2 Arquivo vercel.json

```json
{
  "functions": {
    "main.py": {
      "runtime": "python3.11"
    }
  },
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/main.py"
    }
  ],
  "env": {
    "PROJECT_ID": "seu-project-id",
    "LOCATION": "us-central1",
    "CONTEXT_CACHE_ENABLED": "true"
  }
}
```

## 📊 Configuração de Monitoramento

### 6.1 Google Cloud Monitoring

```bash
# Habilitar APIs de monitoring
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com

# Configurar alertas
gcloud alpha monitoring policies create --policy-from-file=monitoring-policy.yaml
```

### 6.2 Arquivo monitoring-policy.yaml

```yaml
displayName: "Darwin Platform Health"
conditions:
  - displayName: "HTTP 5xx errors"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 5
      duration: "300s"
notificationChannels: []
enabled: true
```

## 🔧 Configuração de Variáveis de Ambiente

### 7.1 Variáveis Obrigatórias

```bash
# Core
PROJECT_ID=seu-gcp-project-id
LOCATION=us-central1
BASE_URL=https://sua-app.run.app

# Segurança
API_KEYS=key1,key2,key3
OPENAI_VERIFICATION_TOKEN=seu-token

# RAG
RAG_ENGINE_ENABLED=true
RAG_ENGINE_ID=seu-rag-engine-id
VECTOR_SEARCH_ENABLED=true
VECTOR_INDEX_ENDPOINT=seu-vector-endpoint

# Cache
CONTEXT_CACHE_ENABLED=true

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### 7.2 Variáveis Opcionais

```bash
# Debug
DEBUG=false

# Memory
MEMORY_STORAGE_DIR=/tmp/darwin-memory

# Timeouts
REQUEST_TIMEOUT=30
RAG_TIMEOUT=60
```

## ✅ Verificação do Deployment

### 8.1 Health Checks

```bash
# Verificar saúde básica
curl https://sua-app.run.app/health

# Status completo
curl https://sua-app.run.app/status

# Testar RAG
curl -X POST https://sua-app.run.app/rag \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-api-key" \
  -d '{"query": "test query"}'
```

### 8.2 Logs

```bash
# Cloud Run logs
gcloud logs read --service=darwin-platform --limit=50

# Logs em tempo real
gcloud logs tail --service=darwin-platform
```

## 🛠️ Troubleshooting

### 9.1 Problemas Comuns

```bash
# 1. Erro de autenticação
# Verificar service account
gcloud iam service-accounts list

# 2. Erro de API não habilitada
# Verificar APIs
gcloud services list --enabled

# 3. Erro de memória
# Aumentar memory no Cloud Run
gcloud run services update darwin-platform --memory 4Gi

# 4. Timeout
# Aumentar timeout
gcloud run services update darwin-platform --timeout 900
```

### 9.2 Debug Local

```bash
# Run local com debug
export DEBUG=true
python main.py

# Testes
pytest tests/test_darwin_platform.py -v

# Verificar dependências
pip check
```

## 🎯 Próximos Passos

1. **Configurar domínio customizado**
2. **Implementar CI/CD com GitHub Actions**
3. **Configurar backup dos dados**
4. **Implementar métricas customizadas**
5. **Configurar alertas avançados**

---

**🎉 Parabéns! Sua plataforma Darwin está no ar!**

Acesse: https://sua-app.run.app/docs para ver a documentação completa da API.