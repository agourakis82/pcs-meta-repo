# MCP Server - Sistema de Pesquisa Acadêmica

*Versão 0.2.1 - Atualizado em 2025-09-14 19:59:31*

## 🎯 Visão Geral

Sistema completo de servidor MCP (Model Context Protocol) para pesquisa acadêmica, com APIs robustas, sistema de testes abrangente e documentação automática.

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
curl -H "Authorization: Bearer YOUR_API_KEY" \
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
