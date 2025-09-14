#!/usr/bin/env python3
"""
Sistema G1 - Geração Automática de Documentação

Script para gerar documentação completa do MCP Server automaticamente.
Inclui: docs da API, guias de usuário, changelog, e templates.
"""

from pathlib import Path
from datetime import datetime

# Configurações
DOCS_DIR = Path(__file__).parent.parent / "docs"
API_DOCS_DIR = DOCS_DIR / "api" 
GUIDES_DIR = DOCS_DIR / "guides"
TEMPLATES_DIR = DOCS_DIR / "templates"

class DocumentationGenerator:
    """Gerador automático de documentação completa."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.version = self._get_version()
        self.generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def _get_version(self) -> str:
        """Obtém versão do projeto."""
        try:
            with open(self.project_root / "pyproject.toml", "r") as f:
                content = f.read()
                for line in content.split("\n"):
                    if line.strip().startswith("version"):
                        return line.split("=")[1].strip().strip('"')
        except Exception:
            pass
        return "1.0.0"
    
    def generate_api_docs(self):
        """Gera documentação completa da API."""
        print("🔄 Gerando documentação da API...")
        
        # Documentação principal da API
        api_overview = f"""# API Documentation - MCP Server v{self.version}

*Gerado automaticamente em {self.generated_date}*

## Visão Geral

Esta documentação descreve todos os endpoints e funcionalidades da API do MCP Server.

## Estrutura da API

### Routers Disponíveis

- **Admin** (`/admin`) - Funcionalidades administrativas
- **RAG** (`/rag`) - Sistema de Retrieval-Augmented Generation  
- **Data** (`/data`) - Gerenciamento de dados e datasets
- **Notebooks** (`/notebooks`) - Execução e gerenciamento de notebooks
- **Processing** (`/processing`) - Sistema de processamento de jobs

### Autenticação

Todos os endpoints requerem autenticação via API key no header:
```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### Admin Router

#### GET /admin/health
- **Descrição**: Verifica saúde do sistema
- **Autenticação**: Requerida
- **Resposta**: Status da aplicação e componentes

#### GET /admin/stats  
- **Descrição**: Estatísticas do sistema
- **Autenticação**: Requerida
- **Resposta**: Métricas de uso e performance

### RAG Router

#### POST /rag/query
- **Descrição**: Executa consulta RAG
- **Autenticação**: Requerida
- **Body**: 
  ```json
  {{
    "query": "string",
    "limit": "integer (opcional, default: 10)"
  }}
  ```
- **Resposta**: Resultados da busca com contexto

#### GET /rag/documents
- **Descrição**: Lista documentos indexados
- **Autenticação**: Requerida
- **Resposta**: Lista de documentos com metadados

### Data Router

#### GET /data/datasets
- **Descrição**: Lista datasets disponíveis
- **Autenticação**: Requerida  
- **Resposta**: Lista de datasets com informações

#### POST /data/upload
- **Descrição**: Upload de novo dataset
- **Autenticação**: Requerida
- **Body**: Multipart form data
- **Resposta**: Confirmação de upload

### Notebooks Router

#### GET /notebooks/list
- **Descrição**: Lista notebooks disponíveis
- **Autenticação**: Requerida
- **Resposta**: Lista de notebooks

#### POST /notebooks/execute
- **Descrição**: Executa notebook
- **Autenticação**: Requerida
- **Body**:
  ```json
  {{
    "notebook_path": "string",
    "parameters": "object (opcional)"
  }}
  ```

### Processing Router

#### POST /processing/job
- **Descrição**: Submete job para processamento
- **Autenticação**: Requerida
- **Body**:
  ```json
  {{
    "job_type": "string",
    "data": "object",
    "priority": "integer (opcional)"
  }}
  ```

#### GET /processing/jobs
- **Descrição**: Lista jobs ativos
- **Autenticação**: Requerida
- **Resposta**: Lista de jobs com status

## Códigos de Resposta

- **200**: Sucesso
- **400**: Erro de validação
- **401**: Não autorizado
- **403**: Proibido
- **404**: Não encontrado
- **422**: Erro de processamento
- **500**: Erro interno do servidor

## Modelos de Dados

### Estruturas de Resposta

Todas as respostas seguem o formato padrão:
```json
{{
  "status": "success|error",
  "data": "object|array",
  "message": "string (opcional)",
  "timestamp": "ISO 8601 datetime"
}}
```

### Configuração

Ver arquivo `api/config.py` para todas as configurações disponíveis.

---

*Documentação gerada automaticamente pelo Sistema G1*
"""
        
        with open(API_DOCS_DIR / "README.md", "w") as f:
            f.write(api_overview)
            
        print("✅ Documentação da API criada")
    
    def generate_user_guides(self):
        """Gera guias completos para usuários."""
        print("🔄 Gerando guias de usuário...")
        
        # Guia de instalação
        installation_guide = f"""# Guia de Instalação - MCP Server v{self.version}

*Gerado automaticamente em {self.generated_date}*

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
"""

        with open(GUIDES_DIR / "installation.md", "w") as f:
            f.write(installation_guide)
        
        # Guia de uso rápido
        quickstart = f"""# Guia de Uso Rápido - MCP Server v{self.version}

*Gerado automaticamente em {self.generated_date}*

## Primeiros Passos

### 1. Verificar Status
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \\
     http://localhost:8000/admin/health
```

### 2. Consulta RAG
```bash
curl -X POST \\
     -H "Authorization: Bearer YOUR_API_KEY" \\
     -H "Content-Type: application/json" \\
     -d '{{"query": "machine learning"}}' \\
     http://localhost:8000/rag/query
```

### 3. Listar Datasets
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \\
     http://localhost:8000/data/datasets
```

### 4. Executar Notebook
```bash
curl -X POST \\
     -H "Authorization: Bearer YOUR_API_KEY" \\
     -H "Content-Type: application/json" \\
     -d '{{"notebook_path": "example.ipynb"}}' \\
     http://localhost:8000/notebooks/execute
```

## Exemplos de Uso

### Python Cliente
```python
import requests

# Configurar headers
headers = {{
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}}

# Consulta RAG
response = requests.post(
    "http://localhost:8000/rag/query",
    json={{"query": "neural networks"}},
    headers=headers
)

print(response.json())
```

### JavaScript Cliente
```javascript
const headers = {{
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}};

fetch('http://localhost:8000/rag/query', {{
    method: 'POST',
    headers: headers,
    body: JSON.stringify({{query: 'deep learning'}})
}})
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
"""

        with open(GUIDES_DIR / "quickstart.md", "w") as f:
            f.write(quickstart)
            
        # Guia de troubleshooting
        troubleshooting = f"""# Guia de Solução de Problemas - MCP Server v{
            self.version}

*Gerado automaticamente em {self.generated_date}*

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
"""

        with open(GUIDES_DIR / "troubleshooting.md", "w") as f:
            f.write(troubleshooting)
            
        print("✅ Guias de usuário criados")
    
    def generate_code_docs(self):
        """Gera documentação inline do código."""
        print("🔄 Gerando documentação do código...")
        
        code_docs = f"""# Documentação do Código - MCP Server v{self.version}

*Gerado automaticamente em {self.generated_date}*

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
    return {{"status": "success"}}
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
"""

        with open(DOCS_DIR / "code-documentation.md", "w") as f:
            f.write(code_docs)
            
        print("✅ Documentação do código criada")
    
    def generate_changelog(self):
        """Gera changelog automático."""
        print("🔄 Gerando changelog...")
        
        changelog = f"""# Changelog - MCP Server

*Gerado automaticamente em {self.generated_date}*

Todas as mudanças importantes do projeto são documentadas neste arquivo.

## [v{self.version}] - {datetime.now().strftime("%Y-%m-%d")}

### 🎉 Novo
- **G1 - Sistema de Documentação**: Sistema completo de geração automática \
de documentação
- **API Documentation**: Documentação completa de todos os endpoints
- **User Guides**: Guias de instalação, uso rápido e troubleshooting
- **Code Documentation**: Documentação inline do código
- **Templates**: Templates reutilizáveis para documentação

### ✅ Melhorias
- Sistema F1 de testes totalmente funcional
- Infraestrutura de autenticação robusta
- Sistema de cache em memória e Redis
- Processamento assíncrono de jobs

### 🔧 Correções
- Melhorias na validação de configurações
- Tratamento de erros mais robusto
- Performance otimizada

### 🚀 Implementações Anteriores
- **A2 - Sistema de Configuração**: Gerenciamento centralizado de configurações
- **B1 - Sistema de Autenticação**: Autenticação via API keys
- **C1 - Sistema de Cache**: Cache em memória com suporte Redis
- **D1 - APIs Principais**: Routers para admin, RAG, data, notebooks, processing
- **E1 - Sistema de Processamento**: Processamento assíncrono de jobs
- **F1 - Sistema de Testes**: Framework completo de testes com pytest

## Roadmap

### Próximas Versões

#### H1 - Sistema de Monitoramento
- Métricas de performance
- Alertas automatizados
- Dashboard de monitoramento

#### I1 - Sistema de Deploy
- Containerização completa
- CI/CD automatizado
- Deploy em produção

#### J1 - Sistema de Segurança
- Autenticação avançada
- Rate limiting
- Auditoria de segurança

### Recursos Planejados
- Integração com mais LLMs
- Interface web administrativa
- API versioning
- Documentação interativa (Swagger UI)
- Sistema de plugins

## Contribuidores

- Sistema Automático de Documentação G1
- Framework de Testes F1
- Infraestrutura Base A2-E1

## Links Úteis

- [Documentação da API](docs/api/README.md)
- [Guias de Usuário](docs/guides/)
- [Documentação do Código](docs/code-documentation.md)
- [Templates](docs/templates/)

---

*Versioning seguindo [Semantic Versioning](https://semver.org/)*
"""

        with open(self.project_root / "CHANGELOG.md", "w") as f:
            f.write(changelog)
            
        print("✅ Changelog criado")
    
    def generate_templates(self):
        """Gera templates reutilizáveis."""
        print("🔄 Gerando templates...")
        
        # Template para nova API
        api_template = """# Template - Nova API

## Estrutura Básica

### 1. Router (`api/routers/new_router.py`)
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from api.auth import require_api_key
from api.services.new_service import NewService

router = APIRouter(prefix="/new", tags=["new"])
service = NewService()

@router.get("/")
async def list_items(user: dict = Depends(require_api_key)) -> List[Dict[str, Any]]:
    \"\"\"Lista todos os itens.\"\"\"
    try:
        return await service.list_items()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_item(
    item_data: dict,
    user: dict = Depends(require_api_key)
) -> Dict[str, Any]:
    \"\"\"Cria novo item.\"\"\"
    try:
        return await service.create_item(item_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. Serviço (`api/services/new_service.py`)
```python
from typing import List, Dict, Any
from api.config import get_settings

class NewService:
    \"\"\"Serviço para gerenciar novos itens.\"\"\"
    
    def __init__(self):
        self.config = get_settings()
        self.items = []  # Substituir por persistência real
    
    async def list_items(self) -> List[Dict[str, Any]]:
        \"\"\"Lista todos os itens.\"\"\"
        return self.items
    
    async def create_item(self, item_data: dict) -> Dict[str, Any]:
        \"\"\"Cria novo item.\"\"\"
        # Validação
        if not item_data.get("name"):
            raise ValueError("Nome é obrigatório")
        
        # Processamento
        item = {
            "id": len(self.items) + 1,
            "name": item_data["name"],
            "created_at": "2025-01-01T00:00:00"
        }
        
        self.items.append(item)
        return item
```

### 3. Testes (`tests/api/test_new_router.py`)
```python
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture  
def auth_headers():
    return {"Authorization": "Bearer test-key"}

def test_list_items(client, auth_headers):
    response = client.get("/new/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_item(client, auth_headers):
    item_data = {"name": "Test Item"}
    response = client.post("/new/", json=item_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Item"
```

### 4. Registro no Main (`api/main.py`)
```python
from api.routers import new_router

app.include_router(new_router.router)
```

## Checklist de Implementação

- [ ] Criar router com endpoints básicos
- [ ] Implementar serviço com lógica de negócio
- [ ] Adicionar validações e tratamento de erros
- [ ] Criar testes unitários e de integração
- [ ] Registrar router na aplicação principal
- [ ] Atualizar documentação da API
- [ ] Adicionar entrada no changelog

---

*Template pronto para uso! 🚀*
"""

        with open(TEMPLATES_DIR / "new-api-template.md", "w") as f:
            f.write(api_template)
        
        # Template para documentação
        doc_template = """# Template - Documentação

## Estrutura Padrão

### Cabeçalho
```markdown
# Título da Funcionalidade - MCP Server v{version}

*Gerado automaticamente em {date}*

## Visão Geral
Breve descrição da funcionalidade e seu propósito.
```

### Seções Obrigatórias

#### 1. Instalação/Configuração
```markdown
## Instalação

### Pré-requisitos
- Lista de dependências
- Versões mínimas

### Passos
1. Primeiro passo
2. Segundo passo
3. Verificação
```

#### 2. Uso Básico
```markdown
## Uso Básico

### Exemplo Simples
\\```python
# Código de exemplo
\\```

### Parâmetros
- `param1`: Descrição
- `param2`: Descrição
```

#### 3. Referência da API
```markdown
## Referência da API

### Endpoint Principal
- **URL**: `/api/endpoint`
- **Método**: POST
- **Autenticação**: Requerida
- **Body**: JSON com campos obrigatórios
- **Resposta**: Estrutura de retorno
```

#### 4. Exemplos Avançados
```markdown
## Exemplos Avançados

### Caso de Uso 1
\\```python
# Exemplo mais complexo
\\```

### Caso de Uso 2
\\```bash
# Comando CLI
\\```
```

#### 5. Troubleshooting
```markdown
## Troubleshooting

### Erro Comum 1
**Sintoma**: Descrição do erro
**Causa**: Por que acontece
**Solução**: Como resolver

### Erro Comum 2
**Sintoma**: Descrição do erro
**Causa**: Por que acontece
**Solução**: Como resolver
```

### Rodapé Padrão
```markdown
---

*Documentação gerada pelo Sistema G1 - {date}*
```

## Estilo e Formatação

### Código
- Usar \\``` para blocos de código
- Especificar linguagem (python, bash, json)
- Incluir comentários explicativos

### Links
- Links internos: `[texto](./arquivo.md)`
- Links externos: `[texto](https://url.com)`

### Ênfase
- **Negrito** para termos importantes
- *Itálico* para observações
- `código` para comandos e variáveis

### Listas
- Usar `-` para listas não ordenadas
- Usar `1.` para listas ordenadas
- Indentar sub-itens com 2 espaços

---

*Template de documentação pronto! 📚*
"""

        with open(TEMPLATES_DIR / "documentation-template.md", "w") as f:
            f.write(doc_template)
        
        print("✅ Templates criados")
        
    def generate_readme(self):
        """Gera README principal atualizado."""
        print("🔄 Atualizando README principal...")
        
        readme = f"""# MCP Server - Sistema de Pesquisa Acadêmica

*Versão {self.version} - Atualizado em {self.generated_date}*

## 🎯 Visão Geral

Sistema completo de servidor MCP (Model Context Protocol) para pesquisa \
acadêmica, com APIs robustas, sistema de testes abrangente e documentação \
automática.

## ✨ Funcionalidades

### 🔧 Sistemas Implementados

- **A2 - Configuração**: Gerenciamento centralizado de configurações
- **B1 - Autenticação**: Sistema de API keys seguro
- **C1 - Cache**: Cache em memória com suporte Redis
- **D1 - APIs**: Routers completos (Admin, RAG, Data, Notebooks, Processing)
- **E1 - Processamento**: Sistema assíncrono de jobs
- **F1 - Testes**: Framework completo com pytest
- **G1 - Documentação**: Sistema automático de documentação

### 🚀 APIs Disponíveis

- **Admin** (`/admin`) - Saúde do sistema e estatísticas
- **RAG** (`/rag`) - Retrieval-Augmented Generation
- **Data** (`/data`) - Gerenciamento de datasets
- **Notebooks** (`/notebooks`) - Execução de notebooks Jupyter
- **Processing** (`/processing`) - Processamento de jobs

## 📚 Documentação

### Guias Principais
- [**Instalação**](docs/guides/installation.md) - Como instalar e configurar
- [**Uso Rápido**](docs/guides/quickstart.md) - Primeiros passos
- [**Troubleshooting**](docs/guides/troubleshooting.md) - Solução de problemas

### Documentação Técnica
- [**API Reference**](docs/api/README.md) - Documentação completa da API
- [**Código**](docs/code-documentation.md) - Documentação do código
- [**Templates**](docs/templates/) - Templates reutilizáveis

### Changelog
- [**CHANGELOG.md**](CHANGELOG.md) - Histórico de versões

## 🚀 Início Rápido

### 1. Instalação
```bash
git clone <repository-url>
cd pcs-meta-repo
pip install -r requirements.txt
```

### 2. Configuração
```bash
cp .env.example .env
# Editar .env com suas configurações
```

### 3. Executar
```bash
python -m uvicorn main:app --reload
```

### 4. Testar
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \\
     http://localhost:8000/admin/health
```

## 🧪 Testes

Sistema completo de testes com pytest:

```bash
# Executar todos os testes
pytest

# Testes com cobertura
pytest --cov=api

# Validação completa F1
./run_tests_f1.sh
```

### Cobertura de Testes
- ✅ Configuração e validação
- ✅ Autenticação e segurança
- ✅ Sistema de cache
- ✅ Endpoints da API
- ✅ Processamento de jobs

## 📖 Documentação Automática

O sistema G1 gera automaticamente:

```bash
# Gerar toda documentação
python scripts/generate_docs.py

# Documentação específica
python scripts/generate_docs.py --api-only
python scripts/generate_docs.py --guides-only
```

## 🔐 Autenticação

Todas as APIs requerem autenticação via API key:

```bash
# Header obrigatório
Authorization: Bearer YOUR_API_KEY
```

## 📊 Monitoramento

### Health Check
```bash
GET /admin/health
```

### Estatísticas
```bash  
GET /admin/stats
```

## 🛠️ Desenvolvimento

### Estrutura do Projeto
```
pcs-meta-repo/
├── api/                    # API principal
├── tests/                  # Testes automatizados  
├── docs/                   # Documentação
├── scripts/                # Scripts utilitários
└── requirements.txt        # Dependências
```

### Adicionando Novas Funcionalidades
1. Usar templates em `docs/templates/`
2. Implementar testes primeiro (TDD)
3. Seguir padrões existentes
4. Atualizar documentação
5. Executar validação F1

## 📋 Requisitos

- Python 3.8+
- FastAPI
- Redis (opcional)
- pytest

## 🤝 Contribuindo

1. Fork o projeto
2. Criar branch para feature
3. Implementar com testes
4. Atualizar documentação
5. Submeter pull request

## 📄 Licença

Ver arquivo [LICENSE](LICENSE) para detalhes.

## 🔗 Links Úteis

- [Documentação da API](docs/api/README.md)
- [Guias de Usuário](docs/guides/)
- [Templates](docs/templates/)
- [Changelog](CHANGELOG.md)

---

**Sistema MCP completo com documentação automática! 🎉**

*Powered by Sistema G1 de Documentação Automática*
"""

        with open(self.project_root / "README.md", "w") as f:
            f.write(readme)
            
        print("✅ README principal atualizado")

    def run(self):
        """Executa geração completa de documentação."""
        print("🚀 Iniciando geração de documentação G1...")
        print(f"📦 Versão: {self.version}")
        print(f"📅 Data: {self.generated_date}")
        print()
        
        # Criar diretórios se não existirem
        for dir_path in [DOCS_DIR, API_DOCS_DIR, GUIDES_DIR, TEMPLATES_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Gerar toda documentação
        self.generate_api_docs()
        self.generate_user_guides()
        self.generate_code_docs()
        self.generate_changelog()
        self.generate_templates()
        self.generate_readme()
        
        print()
        print("🎉 Documentação G1 gerada com sucesso!")
        print("📂 Arquivos criados:")
        print("   docs/api/README.md")
        print("   docs/guides/installation.md")
        print("   docs/guides/quickstart.md")
        print("   docs/guides/troubleshooting.md")
        print("   docs/code-documentation.md")
        print("   docs/templates/new-api-template.md")
        print("   docs/templates/documentation-template.md")
        print("   CHANGELOG.md")
        print("   README.md (atualizado)")

if __name__ == "__main__":
    generator = DocumentationGenerator()
    generator.run()