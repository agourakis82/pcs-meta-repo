# 🤖 Configuração ChatGPT - Conector Sem Autenticação

## ✅ Servidor Remoto Confirmado
- **URL**: `https://mcp.agourakis.med.br`
- **Status**: ✅ Online e funcional
- **Schema**: Disponível em `/actions/schema`
- **Sem Auth**: Configurado para acesso direto

---

## 🔧 Configuração no ChatGPT (Sem Autenticação)

### Método 1: Custom Action (Recomendado)

1. **Acesse ChatGPT** → ⚙️ Settings → Beta Features → Actions

2. **Create new action** com estas configurações:

**Nome**: `PCS RAG++ Research`

**Descrição**: `Sistema avançado de pesquisa científica com literatura indexada`

**Authentication**: `None` (Sem autenticação)

**Schema**: Cole este JSON:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "RAG++ Research API",
    "version": "1.0.0",
    "description": "Sistema avançado de pesquisa científica"
  },
  "servers": [
    {
      "url": "https://mcp.agourakis.med.br"
    }
  ],
  "paths": {
    "/search": {
      "post": {
        "operationId": "searchLiterature",
        "summary": "Buscar literatura científica",
        "description": "Busca híbrida em literatura indexada (168+ papers)",
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
                    "description": "Máximo de resultados"
                  },
                  "search_type": {
                    "type": "string",
                    "enum": ["hybrid", "literature", "memory"],
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
                    "query": {"type": "string"},
                    "results": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "content": {"type": "string"},
                          "type": {"type": "string"},
                          "metadata": {"type": "object"}
                        }
                      }
                    },
                    "sources": {"type": "object"}
                  }
                }
              }
            }
          }
        }
      }
    },
    "/tree/search": {
      "post": {
        "operationId": "treeSearch",
        "summary": "Busca hierárquica estruturada",
        "description": "Busca na árvore de conhecimento organizadas por categorias",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "query": {
                    "type": "string",
                    "description": "Consulta para busca hierárquica"
                  },
                  "strategy": {
                    "type": "string",
                    "enum": ["best_first", "depth_first", "breadth_first", "a_star"],
                    "default": "best_first",
                    "description": "Estratégia de busca na árvore"
                  },
                  "max_results": {
                    "type": "integer",
                    "default": 5,
                    "description": "Máximo de resultados"
                  }
                },
                "required": ["query"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Resultados da busca hierárquica"
          }
        }
      }
    },
    "/health": {
      "get": {
        "operationId": "getSystemHealth",
        "summary": "Status do sistema",
        "description": "Verifica saúde e capacidades do sistema",
        "responses": {
          "200": {
            "description": "Status do sistema",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": {"type": "string"},
                    "capabilities": {
                      "type": "array",
                      "items": {"type": "string"}
                    },
                    "indexed_articles": {"type": "integer"}
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

3. **Salvar** e **Testar** a action

---

### Método 2: Custom GPT (Alternativa)

1. **Criar Custom GPT**:
   - Nome: `PCS Research Assistant`
   - Descrição: `Assistente de pesquisa científica com acesso a literatura indexada`

2. **Instruções**:
```
Você é um assistente de pesquisa científica com acesso a um sistema RAG++ que contém 168+ artigos indexados.

Quando o usuário fizer perguntas sobre pesquisa:
1. Use searchLiterature para busca híbrida na literatura
2. Use treeSearch para busca hierárquica estruturada  
3. Use getSystemHealth para verificar status do sistema

Áreas disponíveis:
- Machine Learning (3 papers)
- Statistics (7 papers) 
- Visualization (14 papers)
- Mathematics (8 papers)

Sempre cite as fontes e forneça contexto científico relevante.
```

3. **Adicionar Actions**: Use o mesmo schema JSON acima

---

## 🎯 Comandos para Testar

### 1. **Verificar Sistema**:
```
"Check the system health and tell me how many articles are indexed"
```

### 2. **Busca Básica**:
```
"Search literature about 'machine learning classification' with 5 results"
```

### 3. **Busca Hierárquica**:
```
"Use tree search to find papers about 'data visualization' with best_first strategy"
```

### 4. **Busca Específica**:
```
"Search for papers about 'deep learning crop disease' using hybrid search"
```

---

## ✅ Vantagens Sem Autenticação

- 🚀 **Configuração Rápida**: Sem tokens ou chaves
- 🔄 **Acesso Direto**: Funciona imediatamente  
- 🌐 **Público**: Acessível por qualquer ChatGPT
- 🔧 **Fácil Teste**: Pode testar via curl também

---

## 🧪 Teste Manual (Opcional)

Para verificar se funciona antes de configurar:

```bash
# Teste básico
curl https://mcp.agourakis.med.br/health

# Teste de busca
curl -X POST https://mcp.agourakis.med.br/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "max_results": 3}'

# Teste tree search  
curl -X POST https://mcp.agourakis.med.br/tree/search \
  -H "Content-Type: application/json" \
  -d '{"query": "statistics", "strategy": "best_first"}'
```

---

## 🎉 Resultado Final

Após configurar, você terá:
- ✅ Acesso direto a 168+ artigos científicos
- ✅ Busca híbrida (literatura + memória)
- ✅ Busca hierárquica estruturada
- ✅ Sem necessidade de autenticação
- ✅ Resposta em tempo real via ChatGPT

**Pronto para usar! 🚀**