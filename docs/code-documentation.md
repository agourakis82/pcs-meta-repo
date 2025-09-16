# Documentação do Código - MCP Server v0.2.1

*Gerado automaticamente em 2025-09-14 19:59:31*

## Estrutura do Projeto

```
pcs-meta-repo/
├── api/                    # API principal
│   ├── __init__.py
│   ├── auth.py            # Sistema de autenticação
│   ├── config.py          # Configurações
│   ├── main.py            # Aplicação FastAPI
│   ├── routers/           # Routers da API
│   │   ├── admin.py       # Endpoints administrativos
│   │   ├── data.py        # Gerenciamento de dados
│   │   ├── notebooks.py   # Execução de notebooks
│   │   ├── processing.py  # Sistema de processamento
│   │   └── rag.py         # Sistema RAG
│   └── services/          # Serviços e lógica de negócio
│       ├── cache.py       # Sistema de cache
│       ├── processing.py  # Processamento de jobs
│       └── rag.py         # Serviço RAG
├── tests/                 # Testes automatizados
├── docs/                  # Documentação
└── scripts/               # Scripts utilitários
```

## Módulos Principais

### api/config.py
Gerencia todas as configurações do sistema:
- Variáveis de ambiente
- Validação de configurações
- Configurações de desenvolvimento/produção

### api/auth.py
Sistema de autenticação:
- Validação de API keys
- Decorators de autorização
- Middleware de segurança

### api/main.py
Aplicação principal FastAPI:
- Configuração da aplicação
- Registro de routers
- Middleware e handlers

### api/services/rag.py
Serviço de RAG (Retrieval-Augmented Generation):
- Indexação de documentos
- Busca semântica
- Geração de respostas

### api/services/cache.py
Sistema de cache:
- Cache em memória
- Integração Redis
- Estratégias de invalidação

### api/services/processing.py
Sistema de processamento:
- Gerenciamento de jobs
- Workers assíncronos
- Monitoramento de status

## Padrões de Código

### Estrutura de Routers
```python
from fastapi import APIRouter, Depends
from api.auth import require_api_key

router = APIRouter(prefix="/example")

@router.get("/endpoint")
async def endpoint(user: dict = Depends(require_api_key)):
    return {"status": "success"}
```

### Estrutura de Serviços
```python
class ExampleService:
    def __init__(self):
        self.config = get_settings()
    
    async def process(self, data: dict) -> dict:
        # Lógica do serviço
        return result
```

### Tratamento de Erros
```python
from fastapi import HTTPException

try:
    result = await service.process(data)
except ValidationError as e:
    raise HTTPException(status_code=422, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail="Internal error")
```

## Contribuindo

### Adicionando Novos Endpoints
1. Criar função no router apropriado
2. Adicionar autenticação via `require_api_key`
3. Implementar lógica no serviço correspondente
4. Adicionar testes em `tests/`
5. Atualizar documentação

### Padrões de Commit
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Mudanças na documentação
- `test:` Adição/modificação de testes
- `refactor:` Refatoração de código

---

*Código bem documentado! 📚*
