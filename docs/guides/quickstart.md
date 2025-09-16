# Guia de Uso Rápido - MCP Server v0.2.1

*Gerado automaticamente em 2025-09-14 19:59:31*

## Primeiros Passos

### 1. Verificar Status
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/admin/health
```

### 2. Consulta RAG
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"query": "machine learning"}' \
     http://localhost:8000/rag/query
```

### 3. Listar Datasets
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/data/datasets
```

### 4. Executar Notebook
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"notebook_path": "example.ipynb"}' \
     http://localhost:8000/notebooks/execute
```

## Exemplos de Uso

### Python Cliente
```python
import requests

# Configurar headers
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

# Consulta RAG
response = requests.post(
    "http://localhost:8000/rag/query",
    json={"query": "neural networks"},
    headers=headers
)

print(response.json())
```

### JavaScript Cliente
```javascript
const headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
};

fetch('http://localhost:8000/rag/query', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({query: 'deep learning'})
})
.then(response => response.json())
.then(data => console.log(data));
```

## Casos de Uso Comuns

### Pesquisa de Literatura
1. Usar `/rag/query` para buscar artigos
2. Filtrar resultados por relevância
3. Extrair citações e referências

### Análise de Dados
1. Upload de datasets via `/data/upload`
2. Executar notebooks de análise
3. Monitorar jobs de processamento

### Automação
1. Configurar webhooks
2. Agendar execuções
3. Monitorar logs e métricas

---

*Pronto para começar! 🚀*
