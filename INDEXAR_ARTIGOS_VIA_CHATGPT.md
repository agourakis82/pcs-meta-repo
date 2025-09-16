# 🤖 Como Indexar Mais Artigos via ChatGPT

## ✅ Status Atual do Sistema
- **Servidor RAG++**: ✅ Ativo na porta 8000
- **Artigos Indexados**: 168 papers
- **Tree Search**: ✅ Operacional com 4 categorias
- **Capacidades**: hybrid_search, literature_search, memory_search, research_storage, knowledge_synthesis

---

## 🚀 Métodos para Indexar Mais Artigos

### Método 1: Via ChatGPT com Custom Action (Recomendado)

#### Configuração da Action no ChatGPT:

1. **Acesse ChatGPT** → Settings → Beta Features → Actions

2. **Criar Nova Action** com esta configuração:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "PCS RAG++ Research API",
    "version": "1.0.0",
    "description": "Sistema avançado de pesquisa científica com indexação automática"
  },
  "servers": [
    {
      "url": "http://agourakis.local:8000",
      "description": "Servidor RAG++ Local"
    }
  ],
  "paths": {
    "/admin/collect-literature": {
      "post": {
        "operationId": "collectLiterature",
        "summary": "Coletar e indexar nova literatura",
        "description": "Busca e indexa automaticamente papers de áreas específicas",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Áreas de pesquisa: machine_learning, statistics, visualization, mathematics, psychiatry, neuroscience"
                  },
                  "max_papers_per_area": {
                    "type": "integer",
                    "default": 10,
                    "description": "Máximo de papers por área"
                  },
                  "min_citation_count": {
                    "type": "integer",
                    "default": 5,
                    "description": "Mínimo de citações por paper"
                  }
                },
                "required": ["areas"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Literatura coletada com sucesso"
          }
        }
      }
    },
    "/search": {
      "post": {
        "operationId": "searchLiterature",
        "summary": "Buscar literatura indexada",
        "description": "Busca híbrida na literatura científica indexada",
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
                    "default": 10
                  },
                  "search_type": {
                    "type": "string",
                    "enum": ["hybrid", "literature", "memory"],
                    "default": "hybrid"
                  }
                },
                "required": ["query"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Resultados da busca"
          }
        }
      }
    },
    "/tree/search": {
      "post": {
        "operationId": "treeSearch",
        "summary": "Busca hierárquica na árvore de conhecimento",
        "description": "Busca estruturada usando tree search",
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
                  "strategy": {
                    "type": "string",
                    "enum": ["best_first", "depth_first", "breadth_first", "a_star"],
                    "default": "best_first"
                  },
                  "max_results": {
                    "type": "integer",
                    "default": 5
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
        "operationId": "getHealth",
        "summary": "Status do sistema",
        "description": "Verifica saúde do sistema RAG++",
        "responses": {
          "200": {
            "description": "Status do sistema"
          }
        }
      }
    }
  }
}
```

### Método 2: Comandos Diretos para ChatGPT

Depois de configurar a action, use estes comandos no ChatGPT:

#### 🔍 **Para Indexar Novos Papers:**
```
"Colete literatura científica nas áreas: ['computational_psychiatry', 'digital_phenotyping', 'neuroimaging'] com máximo de 15 papers por área"
```

#### 📊 **Para Verificar Status:**
```
"Verifique o status do sistema RAG++ e me diga quantos artigos estão indexados"
```

#### 🔎 **Para Buscar Literatura:**
```
"Busque na literatura sobre 'deep learning for depression diagnosis' usando busca híbrida"
```

#### 🌳 **Para Busca Hierárquica:**
```
"Use tree search para encontrar papers sobre 'EEG machine learning' com estratégia best_first"
```

---

## 🎯 Áreas Disponíveis para Coleta

### Principais:
- `machine_learning` - Aprendizado de máquina
- `statistics` - Estatística e análise de dados  
- `visualization` - Visualização de dados
- `mathematics` - Matemática aplicada

### Especializadas:
- `computational_psychiatry` - Psiquiatria computacional
- `digital_phenotyping` - Fenotipagem digital
- `neuroimaging` - Neuroimagem
- `neuroscience` - Neurociência
- `clinical_ai` - IA clínica
- `biomarkers` - Biomarcadores

---

## 📝 Exemplos de Uso no ChatGPT

### 1. **Indexar Papers de Psiquiatria Computacional:**
```
Use collectLiterature para coletar literatura nas áreas:
- computational_psychiatry
- digital_phenotyping  
- clinical_ai

Com máximo de 20 papers por área e mínimo de 10 citações
```

### 2. **Buscar Conhecimento Específico:**
```
Use searchLiterature para buscar sobre "transformer models for EEG analysis" 
com busca híbrida e 15 resultados
```

### 3. **Exploração Hierárquica:**
```
Use treeSearch para encontrar papers sobre "depression biomarkers" 
usando estratégia a_star com 10 resultados
```

---

## 🔧 Troubleshooting

### ❌ **Se a Action não funcionar:**

1. **Verificar conectividade:**
```bash
curl http://127.0.0.1:8000/health
```

2. **Logs do servidor:**
```bash
tail -f ragpp_server.log
```

3. **Reiniciar servidor:**
```bash
pkill -f ragpp_web_server
cd /home/agourakis82/workspace/pcs-meta-repo
nohup python -m uvicorn ragpp.ragpp_web_server:app --host 127.0.0.1 --port 8000 > ragpp_server.log 2>&1 &
```

### ⚠️ **Limitações Atuais:**
- Servidor local (não acessível externamente)
- Precisa configurar túnel ou deploy para uso remoto
- Rate limits nas APIs de literatura (arXiv, Semantic Scholar)

---

## 🚀 Próximos Passos

1. **Configure a Action no ChatGPT** usando o schema acima
2. **Teste com um comando simples** como verificar health
3. **Comece indexando** uma área específica de interesse
4. **Use busca híbrida** para explorar o conteúdo indexado
5. **Refine as consultas** baseado nos resultados

**Pronto! Agora você pode indexar mais artigos diretamente pelo ChatGPT!** 🎉