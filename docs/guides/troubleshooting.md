# Guia de Solução de Problemas - MCP Server v0.2.1

*Gerado automaticamente em 2025-09-14 19:59:31*

## Problemas Comuns

### 1. Erro de Autenticação (401)

**Sintoma**: Resposta "Unauthorized"

**Soluções**:
- Verificar se API key está correta
- Confirmar header Authorization correto
- Validar formato: `Bearer YOUR_API_KEY`

### 2. Servidor Não Inicia

**Sintomas**: Erro ao executar uvicorn

**Soluções**:
```bash
# Verificar dependências
pip install -r requirements.txt

# Verificar porta disponível
netstat -tuln | grep 8000

# Executar com debug
python -m uvicorn main:app --reload --log-level debug
```

### 3. Redis Não Conecta

**Sintoma**: Erro de conexão Redis

**Soluções**:
```bash
# Verificar se Redis está rodando
redis-cli ping

# Iniciar Redis
sudo service redis-server start

# Verificar URL no .env
REDIS_URL=redis://localhost:6379
```

### 4. Performance Lenta

**Sintomas**: Respostas demoradas

**Soluções**:
- Aumentar número de workers
- Configurar cache Redis
- Verificar logs de performance

### 5. Erro de Importação

**Sintoma**: ModuleNotFoundError

**Soluções**:
```bash
# Instalar dependências faltantes
pip install -r requirements.txt

# Verificar PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

## Logs e Debug

### Habilitar Debug
```bash
# No .env
LOG_LEVEL=DEBUG

# Executar com logs detalhados
python -m uvicorn main:app --log-level debug
```

### Monitorar Logs
```bash
# Logs em tempo real
tail -f logs/app.log

# Filtrar erros
grep ERROR logs/app.log
```

## Comandos de Diagnóstico

### Verificar Sistema
```bash
# Status geral
curl http://localhost:8000/admin/health

# Estatísticas
curl -H "Authorization: Bearer KEY" http://localhost:8000/admin/stats
```

### Testar Componentes
```bash
# Testar RAG
python -c "from api.services.rag import RAGService; print('RAG OK')"

# Testar Cache
python -c "from api.services.cache import MemoryCache; print('Cache OK')"
```

## Contato e Suporte

- **Issues**: Criar issue no repositório
- **Logs**: Incluir logs relevantes
- **Ambiente**: Especificar OS, Python version
- **Configuração**: Compartilhar .env (sem chaves)

---

*Problemas resolvidos! ✅*
