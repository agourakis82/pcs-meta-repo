# Configuração Final ChatGPT - PCS-Meta-Repo

✅ **Status**: Validado e Funcional  
🚀 **Servidor**: <https://mcp.agourakis.med.br> (168 artigos indexados)  
🧠 **Cache Multi-IA**: Ativo com transferência cross-AI

## 🎯 Resumo da Configuração

O erro "storeChatGPTContext operation isn't recognized" foi **corrigido**. 
Sistema expandido com **cache inteligente entre diferentes IAs**.

## 🆕 FUNCIONALIDADES AVANÇADAS

### 🔄 Cache Multi-IA
- **Suporte**: ChatGPT, Claude, Copilot, Gemini
- **Transferência Cross-AI**: Contexto entre diferentes sistemas
- **Persistência**: Armazenamento automático de conversas
- **Busca Inteligente**: Recuperação semântica de contextos

### ⚡ Capacidades do Sistema
- Cache inteligente de conversas
- Transferência de contexto entre IAs  
- Sincronização automática
- Análise de importância
- Busca semântica avançada

### Schema OpenAPI Completo - Multi-IA Cache

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "PCS-Meta-Repo Literature Search & Multi-AI Cache API",
    "version": "1.0.0",
    "description": "API para busca híbrida em literatura científica + Cache inteligente entre diferentes IAs"
  },
  "servers": [
    {
      "url": "https://mcp.agourakis.med.br",
      "description": "Servidor de produção RAG++ com Cache Multi-IA"
    }
  ],
  "paths": {
    "/search": {
      "post": {
        "operationId": "searchResearch",
        "summary": "Busca híbrida em literatura científica",
        "description": "Realiza busca semântica e por palavras-chave na base de conhecimento",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "query": {
                    "type": "string",
                    "description": "Consulta de pesquisa"
                  },
                  "max_results": {
                    "type": "integer",
                    "default": 10,
                    "description": "Número máximo de resultados"
                  },
                  "search_type": {
                    "type": "string",
                    "enum": ["semantic", "keyword", "hybrid"],
                    "default": "hybrid",
                    "description": "Tipo de busca"
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
                    "results": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "title": {"type": "string"},
                          "content": {"type": "string"},
                          "score": {"type": "number"},
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
                    }
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
        "summary": "Obtém pesquisas recentes",
        "description": "Retorna artigos e pesquisas recentemente indexados",
        "parameters": [
          {
            "name": "limit",
            "in": "query",
            "schema": {
              "type": "integer",
              "default": 20
            },
            "description": "Número máximo de resultados"
          },
          {
            "name": "categories",
            "in": "query",
            "schema": {
              "type": "string"
            },
            "description": "Filtrar por categorias (opcional)"
          }
        ],
        "responses": {
          "200": {
            "description": "Lista de pesquisas recentes",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "papers": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "title": {"type": "string"},
                          "authors": {"type": "array", "items": {"type": "string"}},
                          "abstract": {"type": "string"},
                          "categories": {"type": "array", "items": {"type": "string"}},
                          "indexed_date": {"type": "string"}
                        }
                      }
                    },
                    "total": {"type": "integer"}
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
        "description": "Verifica saúde do sistema e estatísticas",
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
                    "capabilities": {"type": "array", "items": {"type": "string"}},
                    "indexed_articles": {"type": "integer"},
                    "timestamp": {"type": "string"}
                  }
                }
              }
            }
          }
        }
      }
    },
    "/ai/sessions": {
      "post": {
        "operationId": "createAISession",
        "summary": "Criar sessão de cache multi-IA",
        "description": "Cria nova sessão para cache inteligente entre diferentes IAs",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "ai_type": {
                    "type": "string",
                    "enum": ["chatgpt", "claude", "copilot", "gemini"],
                    "description": "Tipo de IA"
                  },
                  "session_name": {
                    "type": "string",
                    "description": "Nome da sessão"
                  },
                  "context_summary": {
                    "type": "string",
                    "description": "Resumo do contexto inicial"
                  },
                  "user_id": {
                    "type": "string",
                    "default": "default",
                    "description": "ID do usuário"
                  }
                },
                "required": ["ai_type", "session_name"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Sessão criada com sucesso",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "session_id": {"type": "string"},
                    "status": {"type": "string"},
                    "ai_type": {"type": "string"},
                    "cache_enabled": {"type": "boolean"}
                  }
                }
              }
            }
          }
        }
      },
      "get": {
        "operationId": "listAISessions",
        "summary": "Listar sessões de IA",
        "description": "Lista sessões ativas e arquivadas",
        "parameters": [
          {
            "name": "ai_type",
            "in": "query",
            "schema": {"type": "string"},
            "description": "Filtrar por tipo de IA"
          },
          {
            "name": "limit",
            "in": "query",
            "schema": {"type": "integer", "default": 20},
            "description": "Limite de resultados"
          }
        ],
        "responses": {
          "200": {
            "description": "Lista de sessões",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "active_sessions": {"type": "array"},
                    "archived_sessions": {"type": "array"},
                    "total_found": {"type": "integer"}
                  }
                }
              }
            }
          }
        }
      }
    },
    "/ai/sessions/{session_id}/context": {
      "post": {
        "operationId": "storeAIContext",
        "summary": "Armazenar contexto de IA",
        "description": "Salva contexto e mensagens de conversa com IA",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {"type": "string"},
            "description": "ID da sessão"
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "session_id": {"type": "string"},
                  "ai_type": {"type": "string"},
                  "messages": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"},
                        "timestamp": {"type": "string"}
                      }
                    }
                  },
                  "context_summary": {"type": "string"},
                  "importance_score": {"type": "number", "default": 0.5}
                },
                "required": ["session_id", "ai_type", "messages", "context_summary"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Contexto armazenado",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": {"type": "string"},
                    "messages_count": {"type": "integer"},
                    "calculated_importance": {"type": "number"}
                  }
                }
              }
            }
          }
        }
      },
      "get": {
        "operationId": "retrieveAIContext",
        "summary": "Recuperar contexto de IA",
        "description": "Recupera contexto e mensagens de sessão",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {"type": "string"},
            "description": "ID da sessão"
          },
          {
            "name": "include_messages",
            "in": "query",
            "schema": {"type": "boolean", "default": true},
            "description": "Incluir mensagens"
          },
          {
            "name": "max_messages",
            "in": "query",
            "schema": {"type": "integer", "default": 50},
            "description": "Máximo de mensagens"
          }
        ],
        "responses": {
          "200": {
            "description": "Contexto recuperado",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "session_id": {"type": "string"},
                    "ai_type": {"type": "string"},
                    "messages": {"type": "array"},
                    "context_summaries": {"type": "array"}
                  }
                }
              }
            }
          }
        }
      }
    },
    "/ai/transfer": {
      "post": {
        "operationId": "crossAITransfer",
        "summary": "Transferência cross-AI",
        "description": "Transfere contexto entre diferentes IAs",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "source_session_id": {"type": "string"},
                  "target_ai_type": {"type": "string"},
                  "transfer_type": {
                    "type": "string",
                    "enum": ["full", "summary", "selective"],
                    "default": "full"
                  },
                  "include_messages": {"type": "boolean", "default": true},
                  "custom_prompt": {"type": "string"}
                },
                "required": ["source_session_id", "target_ai_type"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Transferência realizada",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": {"type": "string"},
                    "target_session_id": {"type": "string"},
                    "contexts_transferred": {"type": "integer"}
                  }
                }
              }
            }
          }
        }
      }
    },
    "/ai/cache/search": {
      "post": {
        "operationId": "smartCacheSearch",
        "summary": "Busca inteligente no cache",
        "description": "Busca semântica no cache multi-IA",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "query": {"type": "string"},
                  "ai_types": {
                    "type": "array",
                    "items": {"type": "string"}
                  },
                  "time_range": {"type": "integer", "default": 30},
                  "max_results": {"type": "integer", "default": 10}
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
                    "results": {"type": "array"},
                    "search_stats": {"type": "object"}
                  }
                }
              }
            }
          }
        }
      }
    },
    "/ai/cache/stats": {
      "get": {
        "operationId": "getAICacheStats",
        "summary": "Estatísticas do cache multi-IA",
        "description": "Retorna estatísticas do sistema de cache",
        "responses": {
          "200": {
            "description": "Estatísticas do cache",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "cache_stats": {"type": "object"},
                    "system_health": {"type": "object"},
                    "recommendations": {"type": "object"}
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

## 🔧 Configuração no ChatGPT

1. **Acesse**: <https://chatgpt.com/gpts/editor>
2. **Configure Actions**: Cole o schema OpenAPI acima
3. **Authentication**: None (sem autenticação)
4. **Privacy Policy**: `https://mcp.agourakis.med.br/privacy` (opcional)

## ✅ Operações Validadas

| Operação | Status | Teste Realizado |
|----------|--------|-----------------|
| `searchResearch` | ✅ Funcionando | Busca por "machine learning" retornou 3 resultados |
| `getRecentResearch` | ✅ Funcionando | Lista de papers recentes disponível |
| `getSystemHealth` | ✅ Funcionando | Status: healthy, 168 artigos indexados |
| `createAISession` | ✅ Funcionando | 3 sessões criadas (ChatGPT, Claude, Copilot) |
| `storeAIContext` | ✅ Funcionando | 7 mensagens armazenadas com metadados |
| `retrieveAIContext` | ✅ Funcionando | Contexto recuperado com histórico completo |
| `crossAITransfer` | ✅ Funcionando | 2 transferências cross-AI realizadas |
| `smartCacheSearch` | ✅ Funcionando | 10 resultados de busca semântica |
| `getAICacheStats` | ✅ Funcionando | 3 sessões ativas, 5 memórias, 1 transferência |

## 🚫 Operações Removidas

- `storeChatGPTContext`: Causava erro "operation isn't recognized"
- `recallChatGPTContext`: Endpoint inconsistente

## 📊 Capacidades Disponíveis

### 🔍 Busca e Literatura
- **Busca Híbrida**: Combina busca semântica e por palavras-chave
- **168 Artigos Indexados**: Base completa de literatura científica
- **Múltiplos Tipos de Busca**: semantic, keyword, hybrid
- **Filtros por Categoria**: Para pesquisas específicas

### 🧠 Cache Multi-IA  
- **3 Sessões Ativas**: ChatGPT, Claude, Copilot testados
- **Armazenamento Persistente**: Contextos salvos com metadados
- **Transferência Cross-AI**: Contexto entre diferentes sistemas
- **Busca Semântica**: Recuperação inteligente de conversas
- **Análise de Importância**: Score automático de relevância

## 🎯 Exemplos de Uso

### 🔍 Buscar Literatura

```json
{
  "query": "neural networks machine learning",
  "max_results": 5,
  "search_type": "hybrid"
}
```

### 🧠 Criar Sessão de Cache

```json
{
  "ai_type": "chatgpt",
  "session_name": "Análise de EEG",
  "context_summary": "Discussão sobre processamento de sinais neurais"
}
```

### 💾 Armazenar Contexto

```json
{
  "session_id": "a0ce6423-e43e-4970...",
  "ai_type": "chatgpt",
  "messages": [
    {
      "role": "user",
      "content": "Como analisar dados EEG?",
      "timestamp": "2025-09-14T12:34:55Z"
    },
    {
      "role": "assistant", 
      "content": "Para análise de EEG recomendo MNE-Python...",
      "timestamp": "2025-09-14T12:34:56Z"
    }
  ],
  "context_summary": "Discussão sobre análise de EEG com Python"
}
```

### 🔄 Transferência Cross-AI

```json
{
  "source_session_id": "a0ce6423-e43e-4970...",
  "target_ai_type": "claude",
  "transfer_type": "full",
  "include_messages": true,
  "custom_prompt": "Continue esta discussão sobre EEG"
}
```

### 🔍 Busca no Cache

```json
{
  "query": "análise EEG machine learning",
  "ai_types": ["chatgpt", "claude"],
  "time_range": 30,
  "max_results": 10
}
```

### 📊 Pesquisas Recentes

```http
GET /research/recent?limit=10
```

### 🏥 Status do Sistema

```http
GET /health
```

## 🔗 Links Úteis

- **Servidor**: <https://mcp.agourakis.med.br>
- **Health Check**: <https://mcp.agourakis.med.br/health>
- **Schema No-Auth**: <https://mcp.agourakis.med.br/actions/schema/noauth>

---

**✅ Configuração testada e validada em 14/09/2025**  
**🎯 Pronta para uso imediato no ChatGPT**
