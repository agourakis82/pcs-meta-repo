# Guia de Instalação - MCP Server v0.2.1

*Gerado automaticamente em 2025-09-14 19:59:31*

## Pré-requisitos

- Python 3.8+
- pip ou poetry
- Redis (opcional, para cache)

## Instalação Rápida

### 1. Clonar Repositório
```bash
git clone <repository-url>
cd pcs-meta-repo
```

### 2. Instalar Dependências
```bash
# Via pip
pip install -r requirements.txt

# Via poetry (recomendado)
poetry install
```

### 3. Configurar Ambiente
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env
```

### 4. Executar Servidor
```bash
# Desenvolvimento
python -m uvicorn main:app --reload

# Produção
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Configuração Avançada

### Variáveis de Ambiente

- `API_KEYS`: Chaves de API (separadas por vírgula)
- `REDIS_URL`: URL do Redis (opcional)
- `LOG_LEVEL`: Nível de log (DEBUG, INFO, WARNING, ERROR)
- `MAX_WORKERS`: Número máximo de workers

### Cache Redis

Para habilitar cache Redis:
```bash
# Instalar Redis
sudo apt install redis-server

# Configurar URL no .env
REDIS_URL=redis://localhost:6379
```

### Autenticação

Configurar chaves de API no arquivo `.env`:
```
API_KEYS=key1,key2,key3
```

## Verificação

Testar instalação:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/admin/health
```

---

*Instalação completada com sucesso! 🎉*
