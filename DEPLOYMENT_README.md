# 🚀 Deployment - Darwin Platform

Guia rápido para fazer deployment da plataforma Darwin em diferentes ambientes.

## 🎯 Deployment Rápido

### 1. Desenvolvimento Local (Mais Rápido)

```bash
# Execute o script master
./deploy.sh

# Escolha opção 4 (Desenvolvimento Python direto)
# Ou opção 1 (Docker local)
```

### 2. Google Cloud Run (Produção Recomendada)

```bash
# Configure o gcloud primeiro
gcloud auth login
gcloud config set project SEU-PROJECT-ID

# Execute o deployment
./deploy-gcp.sh
```

### 3. Railway (Mais Simples)

```bash
# Execute o deployment
./deploy-railway.sh
```

## 📋 Pré-requisitos Mínimos

### Para desenvolvimento local:
- Python 3.11+
- Docker (opcional)

### Para Google Cloud:
- Google Cloud CLI
- Projeto GCP com billing ativado
- APIs habilitadas (o script faz automaticamente)

### Para Railway:
- Conta no Railway
- Node.js (para instalar CLI)

## ⚡ Scripts de Deployment

| Script | Descrição | Tempo | Complexidade |
|--------|-----------|-------|--------------|
| `./deploy.sh` | Menu interativo | - | ⭐ |
| `./deploy-local.sh` | Docker local | 2 min | ⭐ |
| `./deploy-gcp.sh` | Google Cloud Run | 5 min | ⭐⭐ |
| `./deploy-railway.sh` | Railway | 3 min | ⭐ |

## 🔧 Configuração Básica

### Variáveis de Ambiente Essenciais

```bash
# Core (obrigatórias)
PROJECT_ID=seu-gcp-project
LOCATION=us-central1
API_KEYS=key1,key2,key3

# Features (opcionais)
CONTEXT_CACHE_ENABLED=true
RAG_ENGINE_ENABLED=true
DEBUG=false
```

### Para Produção

```bash
# Google Cloud
export PROJECT_ID="seu-project-real"
export RAG_ENGINE_ID="seu-rag-engine"
export VECTOR_INDEX_ENDPOINT="seu-vector-endpoint"

# API Keys
export API_KEYS="chave-producao-1,chave-producao-2"
export OPENAI_VERIFICATION_TOKEN="token-real"
```

## ✅ Verificação Rápida

Após qualquer deployment, teste:

```bash
# Health check
curl YOUR_URL/health

# Documentação
open YOUR_URL/docs

# Teste básico da API
curl -X POST YOUR_URL/rag \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-api-key" \
  -d '{"query": "teste"}'
```

## 🚨 Troubleshooting Rápido

### Erro de Autenticação (GCP)
```bash
gcloud auth application-default login
```

### Erro de Permissões
```bash
# Verificar service account
gcloud iam service-accounts list
```

### Container não inicia
```bash
# Ver logs
docker logs darwin-app
```

### API não responde
```bash
# Verificar health
curl YOUR_URL/health -v
```

## 📊 Monitoramento

### Logs em tempo real:

```bash
# Google Cloud Run
gcloud logs tail --service=darwin-platform

# Docker local
docker logs darwin-app -f

# Railway
railway logs
```

### Métricas:

- Health: `/health`
- Status: `/status`
- Metrics: `/metrics` (se configurado)

## 🎉 Próximos Passos

1. **Configure domínio customizado**
2. **Setup CI/CD com GitHub Actions** (já incluído)
3. **Configure alertas**
4. **Backup dos dados**

---

**💡 Dica**: Use o script `./deploy.sh` para um menu interativo que guia todo o processo!