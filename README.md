# PCS Meta-Repo / Darwin RAG++ Platform

![Coverage](coverage.svg)
![Concept DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.16921951-blue)

#### Versão

Versão v5.0.0 — Atualizado em 2025-09-16

## � v5.0 Highlights

| Área | Destaque |
|------|----------|
| Darwin RAG++ | Plataforma integrada de RAG com discovery iterativo e monitoramento |
| Vertex (opt-in) | Uso opcional de Vertex AI para embeddings e geração |
| Notebooks Didáticos | Pipeline multimodal real (KEC + SWOW + ZuCo EEG/ET), reasoning iterativo, discovery monitoring, index lifecycle |
| Segurança | Postura documentada (auth, rate limiting, secrets, compliance) |
| Qualidade | Integração contínua com testes condicionais BigQuery/Vertex/Cloud Run & pipeline |
| Governança | Release checklist, quality gates (Q1–Q10), status report consolidado |

### Impacto Científico & Técnico

- Fortalece reproducibilidade: notebooks executáveis com dados reais (nenhum placeholder sintético)
- Escalabilidade sem alterar backend histórico: todas as adições são não-invasivas
- Observabilidade de descoberta: métricas de novidade, entropia e cobertura semântica
- Facilita extensões futuras (symbolic-first) mantendo isolamento do core Darwin

### Limitações & Riscos (Transparência)

- Dependência de serviços externos (Vertex/BigQuery) pode introduzir variabilidade de latência
- Métricas de novidade ainda sensíveis a distribuição de idiomas no SWOW
- Parser ZuCo .mat robusto mas validações semânticas adicionais (artefatos oculomotores) ainda pendentes
- Ausência de normalização cross-línguas aprofundada no pipeline (etapa futura)

### Próximos Passos (Roadmap Curto)

1. Normalização linguística avançada (embeddings multilíngues comparáveis)
2. Enriquecimento de análises EEG com janelas dinâmicas adaptativas
3. Módulo de avaliação automática de explicabilidade das respostas RAG
4. Exportador padronizado de relatórios de descoberta (JSON + Markdown)

---

## 🎯 Visão Geral

Sistema consolidado para pesquisa acadêmica e experimentação RAG simbólico‑primeiro. A partir da v5.0 incorpora a camada Darwin RAG++ (index lifecycle, reasoning iterativo, discovery monitoring) preservando compatibilidade com fluxos anteriores.

## ✨ Funcionalidades Principais

### 🔧 Sistemas Implementados

- **Darwin RAG++**: Indexação, reasoning iterativo, discovery e monitoramento de novidade
- **Vertex Opt-In**: Embeddings / geração condicionais via variáveis de ambiente
- **A2 - Configuração**: Gerenciamento centralizado de configurações
- **B1 - Autenticação**: API keys e princípios mínimos de exposição
- **C1 - Cache**: In-memory + suporte Redis
- **D1 - APIs**: Routers (Admin, RAG, Data, Notebooks, Processing, Discovery)
- **E1 - Processamento**: Jobs assíncronos
- **F1 - Testes**: Suite com integração condicional BigQuery/Vertex/Cloud Run
- **G1 - Documentação**: Geração automática + notebooks didáticos

### 🚀 APIs Disponíveis (Resumo)

- **Admin** (`/admin`) - Saúde e estatísticas
- **RAG** (`/rag`) - Retrieval-Augmented Generation clássico
- **RAG Plus Iterativo** (`/rag-plus/iterative`) - Raciocínio em múltiplos passos
- **Discovery** (`/rag-plus/discovery`) - Ciclos de exploração e novidade
- **Data** (`/data`) - Gestão de datasets
- **Notebooks** (`/notebooks`) - Execução
- **Processing** (`/processing`) - Jobs

## 📚 Documentação

### Guias Principais

- [**Instalação**](docs/guides/installation.md) - Como instalar e configurar
- [**Uso Rápido**](docs/guides/quickstart.md) - Primeiros passos
- [**Troubleshooting**](docs/guides/troubleshooting.md) - Solução de problemas

### Documentação Técnica

- [**Darwin Platform**](docs/darwin_platform.md) - Arquitetura, índices, contratos de dados
- [**Darwin API**](docs/darwin_api.md) - Endpoints, payloads e códigos de erro
- [**Vector Engine**](docs/vector_engine.md) - BigQuery + embeddings
- [**Segurança**](docs/darwin_security.md) - Postura e checklist
- [**API Reference**](docs/api/README.md)
- [**Código**](docs/code-documentation.md)
- [**Templates**](docs/templates/)

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

## 🧪 Testes e Qualidade

Sistema completo de testes com pytest:

```bash
# Executar todos os testes
pytest

# Testes com cobertura
pytest --cov=api

# Validação completa F1
./run_tests_f1.sh
```

### Cobertura de Testes (Áreas Principais)

- Configuração e validação
- Autenticação e segurança
- Cache
- Endpoints principais
- Processamento de jobs
- Pipeline multimodal (condicional)
- Reasoning iterativo e discovery (condicional)

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

## 📊 Monitoramento e Discovery

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

```text
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

Darwin RAG++ v5.0 entregue com foco em reproducibilidade e expansão simbólica.

Powered by Sistema G1 de Documentação Automática + Quality Gates Q1–Q10
