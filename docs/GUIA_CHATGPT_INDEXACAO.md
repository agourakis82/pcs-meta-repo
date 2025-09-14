# 🤖 Guia Rápido: Indexar Artigos via ChatGPT

## ✅ Sistema Atual
- **Status**: ✅ Ativo no localhost:8000  
- **Literatura**: 168+ artigos indexados
- **Tree Search**: 5 nós organizados hierarquicamente
- **Capacidades**: Busca híbrida, literatura, memória

---

## 🚀 Como Usar no ChatGPT

### 1. **Configurar Action no ChatGPT**

No ChatGPT, vá em **Settings → Actions → Create new action** e use:

**URL Base**: `http://127.0.0.1:8000` (se local) ou sua URL pública

**Schema OpenAPI**:
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "PCS RAG++ API",
    "version": "1.0.0"
  },
  "servers": [{"url": "http://127.0.0.1:8000"}],
  "paths": {
    "/search": {
      "post": {
        "operationId": "searchLiterature",
        "summary": "Buscar literatura científica",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "query": {"type": "string"},
                  "max_results": {"type": "integer", "default": 10},
                  "search_type": {"type": "string", "enum": ["hybrid", "literature", "memory"], "default": "hybrid"}
                },
                "required": ["query"]
              }
            }
          }
        },
        "responses": {"200": {"description": "Results"}}
      }
    },
    "/tree/search": {
      "post": {
        "operationId": "treeSearch",
        "summary": "Busca hierárquica na árvore",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "query": {"type": "string"},
                  "strategy": {"type": "string", "enum": ["best_first", "depth_first", "breadth_first"], "default": "best_first"},
                  "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
              }
            }
          }
        },
        "responses": {"200": {"description": "Results"}}
      }
    },
    "/health": {
      "get": {
        "operationId": "getHealth",
        "summary": "Status do sistema",
        "responses": {"200": {"description": "Health status"}}
      }
    }
  }
}
```

### 2. **Comandos para ChatGPT**

#### 🔍 **Buscar Literatura**:
```
"Search literature about 'machine learning in psychiatry' with max 10 results"
```

#### 🌳 **Busca Hierárquica**:
```
"Use tree search to find papers about 'digital phenotyping' with best_first strategy"
```

#### 📊 **Status do Sistema**:
```
"Check the health status of the RAG++ system"
```

### 3. **Áreas Disponíveis**

- **Machine Learning**: 3 papers (crop classification, causal inference, etc.)
- **Statistics**: 7 papers (análise estatística, regressão)  
- **Visualization**: 14 papers (gráficos, visual analytics)
- **Mathematics**: 8 papers (otimização, métodos numéricos)

---

## 🔧 Para Indexar Mais Artigos

### Método 1: Executar Collector Diretamente
```bash
cd /home/agourakis82/workspace/pcs-meta-repo
python scripts/advanced_literature_collector.py
```

### Método 2: Via Script Personalizado
```bash
# Psiquiatria computacional
python chatgpt_literature_indexer.py psychiatry

# IA clínica  
python chatgpt_literature_indexer.py clinical

# Métodos quantitativos
python chatgpt_literature_indexer.py quantitative
```

### Método 3: Adicionar Papers Manualmente
```bash
# Use o populate_tree_with_papers.py para adicionar papers coletados
python populate_tree_with_papers.py
```

---

## 🎯 Exemplos de Queries

### Para Psiquiatria Computacional:
- `"Search for computational psychiatry research"`
- `"Find digital phenotyping studies"`  
- `"Look for neuroimaging machine learning papers"`

### Para IA/ML Geral:
- `"Search for deep learning classification"`
- `"Find transfer learning applications"`
- `"Look for transformer models research"`

### Para Análise de Dados:
- `"Search for statistical modeling papers"`
- `"Find data visualization techniques"`
- `"Look for optimization algorithms"`

---

## ⚡ Status Atual do Servidor

```bash
# Verificar se está rodando
curl http://127.0.0.1:8000/health

# Ver estrutura da árvore
curl http://127.0.0.1:8000/tree/structure | jq '.total_nodes'

# Restart se necessário
pkill -f ragpp_web_server
cd /home/agourakis82/workspace/pcs-meta-repo
nohup python -m uvicorn ragpp.ragpp_web_server:app --host 127.0.0.1 --port 8000 > ragpp_server.log 2>&1 &
```

## ✅ Pronto para Usar!

Agora você pode:
1. **Buscar** na literatura existente (168+ papers)
2. **Indexar** mais artigos usando os scripts
3. **Explorar** hierarquicamente via tree search
4. **Integrar** com ChatGPT para queries avançadas

**🎉 Sistema totalmente funcional para indexação via ChatGPT!**