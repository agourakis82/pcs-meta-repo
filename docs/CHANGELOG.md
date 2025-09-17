# Changelog - MCP Server

*Gerado automaticamente em 2025-09-14 19:59:31*

Todas as mudanças importantes do projeto são documentadas neste arquivo.

## [v0.2.1] - 2025-09-14

### 🎉 Novo
- **G1 - Sistema de Documentação**: Sistema completo de geração automática de documentação
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

## [v5.0.0] - 2025-09-16

### Added

- Darwin RAG++ platform (index lifecycle, iterative reasoning, discovery monitoring)
- Vertex AI opt-in integration (embeddings + generation via env toggles)
- Multimodal real-data pipeline notebook (KEC + SWOW multilíngue + ZuCo EEG/ET) sem placeholders
- ZuCo .mat robust parser + MI parametrização (env `KEC_MI_TOP_N`)
- Discovery & iterative reasoning integration tests (condicionais)
- CI workflow `darwin-integration.yml` para BigQuery / Vertex / Cloud Run / Pipeline
- Vector engine documentation (`docs/vector_engine.md`)
- Segurança e compliance doc (`docs/darwin_security.md`)
- Release checklist (`DARWIN_RELEASE_CHECKLIST.md`), Quality Gates (`QUALITY_GATES_Q1_Q10.md`), Status Report (`DARWIN_STATUS_REPORT.md`)
- New docs: `docs/darwin_platform.md`, `docs/darwin_api.md`, infra docs Vertex & schema SQL

### Changed

- README reestruturado com v5.0 Highlights, impacto, limitações e roadmap curto
- Atualização de metadados (metadata.yaml, zenodo.json, CITATION.cff placeholders)
- Ampliação de cobertura de testes para endpoints RAG Plus / discovery

### Deprecated

- Nenhum módulo formalmente deprecado; planeja-se migração gradual de rotas legacy RAG para camada Darwin unificada em futura versão.

### Fixed

- Ajustes de lint Markdown e consistência terminológica (RAG vs RAG Plus)
- Diagnóstico build LaTeX (ausência `abntex2.cls`) documentado

### Security

- Documentação explícita de autenticação, rate limiting esperado e gerenciamento de segredos

### Notes

- Todas as adições são não-invasivas: backend Darwin existente não modificado
- Próximas melhorias: normalização linguística SWOW, métricas EEG avançadas, explicabilidade automática
