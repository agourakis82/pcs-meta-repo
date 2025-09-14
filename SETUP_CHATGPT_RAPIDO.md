# 🚀 CONFIGURAÇÃO RÁPIDA: ChatGPT Sem Auth

## 📋 Passos Simples

### 1. No ChatGPT:
- Settings → Beta Features → Actions
- **Create new action**

### 2. Configuração:
- **Nome**: `PCS Research`
- **Auth**: `None` (sem autenticação)  
- **Schema URL**: `https://mcp.agourakis.med.br/actions/schema/noauth`

### 3. Ou cole o schema diretamente:
```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "PCS RAG++ Research",
    "version": "1.0.0"
  },
  "servers": [{"url": "https://mcp.agourakis.med.br"}],
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
                  "search_type": {"type": "string", "enum": ["hybrid", "literature"], "default": "hybrid"}
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
        "responses": {"200": {"description": "Health"}}
      }
    }
  }
}
```

## ✅ Teste Imediato

Após configurar, teste com:

```
"Check system health and search for machine learning papers"
```

## 🎯 Comandos de Exemplo

- `"Search literature about computational psychiatry"`
- `"Find papers on data visualization"`  
- `"Look for machine learning research"`
- `"Check how many articles are indexed"`

## ✅ Resultado
- ✅ 168+ artigos científicos acessíveis
- ✅ Busca híbrida funcionando
- ✅ Sem necessidade de tokens
- ✅ Resposta instantânea

**Pronto em 2 minutos! 🎉**