# Darwin RAG++ Platform (v5.0)

## 1. Visão Geral

A camada Darwin RAG++ adiciona index lifecycle, reasoning iterativo e discovery monitoring sem modificar o backend legado. Tudo é opt-in via variáveis de ambiente e notebooks, garantindo isolamento e fácil rollback.

## 2. Arquitetura Lógica

```text
[Clients]
   | REST/HTTP
[FastAPI Routers]
   ├─ /rag (baseline)
   ├─ /rag-plus/iterative (multi-step reasoning)
   ├─ /rag-plus/discovery (ciclos de exploração)
   └─ /admin, /data, /processing
	|
[Vector Engine - BigQuery + Embeddings]
	|
[Storage: BigQuery Tables / External Buckets]
	|
[Datasets: KEC, SWOW, ZuCo EEG/ET]
```

## 3. Index Layout (Vector Engine)

Tabela recomendada `project.dataset.documents`:

- `doc_id` STRING PK lógico
- `title` STRING
- `content` STRING
- `modality` STRING (text|eeg|et)
- `lang` STRING ISO
- `embedding` ARRAY<FLOAT64>
- `entropy` FLOAT64 (opcional)
- `novelty_score` FLOAT64 (atualizado discovery)
- `created_at` TIMESTAMP

## 4. Contratos de Dados

| Fonte | Formato | Normalização | Validação |
|-------|---------|--------------|-----------|
| KEC | CSV | Conversão métrica/float | Schema estrito |
| SWOW | CSV/TSV | Lowercase + trim | Frequências >=1 |
| ZuCo EEG | MAT/CSV | Segmentação trial | Dimensões consistentes |
| ZuCo ET | CSV | Alinhamento tokens | Timestamps ordenados |

Falhas = abort imediata (fail-fast) para preservar integridade analítica.

## 5. Reasoning Iterativo

Endpoint `/rag-plus/iterative` executa ciclos controlados (`max_steps`). Cada passo registra contexto incremental e justificativa. Métricas: latência por passo, tokens adicionais, número de reconsultas.

## 6. Discovery Monitoring

Endpoint `/rag-plus/discovery` ou notebook fallback. Combina:

- Densidade vetorial local (k-NN radius)
- Divergência lexical (KEC/SWOW)
- Entropia incremental

Atualiza `novelty_score` ou gera relatório isolado.

## 7. Ciclo de Index Lifecycle

1. Ingestão batch inicial
2. Geração de embeddings (Vertex ou local)
3. Escrita BigQuery (schema consistente)
4. Consultas ANN / filtros de modalidade/idioma
5. Atualizações incrementais append-only
6. Discovery recalcula novelty subset afetado

## 8. Variáveis de Ambiente

| VAR | Uso | Obrigatório |
|-----|-----|-------------|
| `GCP_PROJECT_ID` | Projeto GCP | Sim (BigQuery) |
| `RAG_DATASET_ID` | Dataset BigQuery | Sim |
| `RAG_TABLE_ID` | Tabela documentos | Sim |
| `DARWIN_API_BASE` | Base API Darwin | Opcional |
| `DARWIN_API_KEY` | Auth | Sim para chamadas |
| `KEC_MI_TOP_N` | Limite MI | Opcional |
| `ZUCO_DATA_DIR` | Dados ZuCo | Pipeline |
| `SWOW_DATA_DIR` | Dados SWOW | Pipeline |
| `SWOW_LANGS` | Idiomas SWOW | Subset |
| `NOVELTY_THRESHOLD` | Sinal discovery | Opcional |

## 9. Segurança

- Rotas pré-existentes intocadas
- Chaves expostas apenas via header (Bearer)
- Recomenda-se gateway externo para rate limiting

## 10. Reprodutibilidade

- Fail-fast para dados ausentes
- Parametrização MI reduz custo
- Sem artefatos sintéticos no pipeline

## 11. Limitações

- Falta de alinhamento vetorial cross-línguas
- Histórico discovery não persistido (snapshot only)
- EEG sem filtros adaptativos avançados

## 12. Roadmap

| Item | P | Descrição |
|------|---|-----------|
| Cross-lingual alignment | Alta | Ajuste espaço semântico multi-idioma |
| Discovery history store | Média | Persistir evolução novelty |
| EEG dynamic windows | Média | Segmentos adaptativos |
| Explainability scoring | Média | Métricas automáticas de passo |

## 13. Referências

- SWOW dataset
- ZuCo (Hollenstein et al.)
- Sandve et al. (2013) Reprodutibilidade

---
Darwin RAG++ v5.0 — Documentação de plataforma.
