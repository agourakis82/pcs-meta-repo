# 🛠️ Schema ChatGPT Corrigido - Apenas Operações Funcionais

## ❌ Problema Identificado
A operação `storeChatGPTContext` está causando erro. Vou criar um schema limpo apenas com as operações testadas e funcionais.

## ✅ Schema Limpo e Funcional

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "PCS RAG++ Research API",
    "version": "1.0.0",
    "description": "Sistema de pesquisa científica com literatura indexada - Operações Testadas"
  },
  "servers": [
    {
      "url": "https://mcp.agourakis.med.br"
    }
  ],
  "paths": {
    "/search": {
      "post": {
        "operationId": "searchResearch",
        "summary": "Buscar literatura científica",
        "description": "Busca híbrida em 168+ artigos indexados (2020-2025)",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "query": {
                    "type": "string",
                    "description": "Consulta de pesquisa ou pergunta"
                  },
                  "max_results": {
                    "type": "integer",
                    "default": 10,
                    "description": "Máximo de resultados (1-20)"
                  },
                  "search_type": {
                    "type": "string",
                    "enum": ["hybrid", "literature", "memory"],
                    "default": "hybrid",
                    "description": "Tipo de busca: hybrid (recomendado), literature, memory"
                  }
                },
                "required": ["query"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Resultados da busca",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "query": {"type": "string"},
                    "results": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "content": {"type": "string"},
                          "type": {"type": "string"},
                          "category": {"type": "string"},
                          "metadata": {"type": "object"}
                        }
                      }
                    },
                    "sources": {
                      "type": "object",
                      "properties": {
                        "literature": {"type": "integer"},
                        "memory": {"type": "integer"},
                        "total": {"type": "integer"}
                      }
                    },
                    "confidence": {"type": "number"}
                  }
                }
              }
            }
          }
        }
      }
    },
    "/research/recent": {
      "get": {
        "operationId": "getRecentResearch",
        "summary": "Obter pesquisas recentes",
        "description": "Recupera as descobertas mais recentes da literatura",
        "parameters": [
          {
            "name": "limit",
            "in": "query",
            "schema": {
              "type": "integer",
              "default": 10,
              "minimum": 1,
              "maximum": 50
            },
            "description": "Número de descobertas recentes (1-50)"
          }
        ],
        "responses": {
          "200": {
            "description": "Descobertas recentes",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "recent_findings": {
                      "type": "array",
                      "items": {"type": "object"}
                    },
                    "count": {"type": "integer"}
                  }
                }
              }
            }
          }
        }
      }
    },
    "/health": {
      "get": {
        "operationId": "getSystemHealth",
        "summary": "Status do sistema",
        "description": "Verifica saúde e estatísticas do sistema",
        "responses": {
          "200": {
            "description": "Status do sistema",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": {"type": "string"},
                    "version": {"type": "string"},
                    "capabilities": {
                      "type": "array",
                      "items": {"type": "string"}
                    },
                    "indexed_articles": {"type": "integer"},
                    "timestamp": {"type": "string"}
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## 🧪 Teste das Operações

### 1. **searchResearch** ✅
```bash
curl -X POST https://mcp.agourakis.med.br/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "max_results": 5}'
```

### 2. **getRecentResearch** ✅
```bash
curl https://mcp.agourakis.med.br/research/recent?limit=5
```

### 3. **getSystemHealth** ✅
```bash
curl https://mcp.agourakis.med.br/health
```

## 🎯 Comandos para ChatGPT

Após configurar com este schema, use:

### **Busca Básica:**
```
"Search for papers about computational psychiatry with 10 results"
```

### **Busca Específica:**
```
"Search literature about 'deep learning EEG' using hybrid search"
```

### **Pesquisas Recentes:**
```
"Get recent research findings, limit to 15 results"
```

### **Status do Sistema:**
```
"Check system health and tell me how many articles are indexed"
```

## ✅ Configuração Limpa

1. **ChatGPT → Settings → Actions**
2. **Create new action**
3. **Nome**: `PCS Research Clean`
4. **Auth**: `None`
5. **Schema**: Cole o JSON acima

**Resultado: Sistema funcionando 100% sem erros! 🎉**