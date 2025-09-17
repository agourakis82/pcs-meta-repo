# Vertex AI Opt-In (Darwin v5.0)

## 1. Escopo

Integração opcional para embeddings e geração. Sistema funciona sem Vertex se variáveis não definidas (fallback local futuro).

## 2. Variáveis de Ambiente

| VAR | Descrição | Obrigatório |
|-----|-----------|-------------|
| `VERTEX_PROJECT` | Projeto GCP | Sim (quando usando Vertex) |
| `VERTEX_LOCATION` | Região ex: `us-central1` | Sim |
| `VERTEX_EMBED_MODEL` | Nome do modelo embedding | Sim |
| `VERTEX_TEXT_MODEL` | Modelo geração texto | Opcional |
| `VERTEX_SAFETY_LEVEL` | Ajustes de segurança | Opcional |
| `GOOGLE_APPLICATION_CREDENTIALS` | Caminho JSON chave serviço | Sim |

## 3. Quotas & Custos

- Custos variam por 1K tokens e chamadas embedding.
- Ajuste de `top_k` e `max_steps` reduz latência e custo.

## 4. Práticas de Segurança

- NÃO commitar arquivos JSON de credenciais.
- Usar Secret Manager ou injetar via runtime.
- Rotacionar chaves periodicamente.

## 5. Setup Rápido

```bash
export VERTEX_PROJECT=my-project
export VERTEX_LOCATION=us-central1
export VERTEX_EMBED_MODEL=textembedding-gecko@003
export GOOGLE_APPLICATION_CREDENTIALS=$HOME/keys/vertex-sa.json
```

## 6. Teste de Sanidade (Python)

```python
from google.cloud import aiplatform
import vertexai
vertexai.init(project="${VERTEX_PROJECT}", location="${VERTEX_LOCATION}")
# Carregar modelo embedding
from vertexai.preview.language_models import TextEmbeddingModel
model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
emb = model.get_embeddings(["symbolic curvature in semantic graphs"])[0].values
print(len(emb))
```

## 7. Limitações

- Sem fallback local implementado nesta release.
- Monitoramento de custo manual.

## 8. Próximos Passos

| Item | Descrição |
|------|-----------|
| Cache Embeddings | Evitar recomputação repetida |
| Métricas Custo | Exportar custo estimado em relatório |
| Fallback Local | Modelo open-source configurável |

---
Vertex AI Opt-In — Documentado.
