# Darwin API (RAG++) v5.0

## 1. Escopo

Extensão não-invasiva adicionando endpoints `/rag-plus/*` para reasoning iterativo e discovery. Mantém compatibilidade com `/rag` clássico.

## 2. Autenticação

Todas as requisições: header `Authorization: Bearer <API_KEY>`.

## 3. Endpoints Principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/rag` | Consulta RAG básica |
| POST | `/rag-plus/iterative` | Reasoning multi-passo controlado |
| POST | `/rag-plus/discovery/start` | Inicia ciclo discovery (se habilitado) |
| POST | `/rag-plus/discovery/step` | Executa passo incremental |
| GET  | `/rag-plus/discovery/status` | Estado atual de métricas |
| POST | `/rag-plus/discovery/stop` | Finaliza ciclo discovery |

## 4. Modelos de Requisição/Resposta

### 4.1 /rag (POST)

Request (JSON):

```json
{
	"query": "Explain symbolic curvature in semantic networks",
	"top_k": 5,
	"lang": "en"
}
```
Response (exemplo simplificado):

```json
{
	"query": "Explain symbolic curvature in semantic networks",
	"results": [
		{"doc_id": "d1", "score": 0.82, "snippet": "Curvature relates to..."}
	],
	"answer": "Symbolic curvature captures...",
	"citations": ["d1"]
}
```

### 4.2 /rag-plus/iterative (POST)

Request:

```json
{
	"query": "Relate EEG entropy to SWOW lexical diversity",
	"max_steps": 4,
	"temperature": 0.2
}
```
Resposta:

```json
{
	"query": "Relate EEG entropy...",
	"steps": [
		{"step": 1, "thought": "Check baseline EEG entropy", "evidence_docs": ["eeg_12"], "partial_answer": "Baseline entropy shows..."},
		{"step": 2, "thought": "Cross-reference SWOW diversity", "evidence_docs": ["swow_en_34"], "partial_answer": "Lexical diversity indicates..."}
	],
	"final_answer": "EEG entropy correlates with lexical diversity via...",
	"metadata": {"latency_ms": 1834}
}
```

### 4.3 Discovery Ciclo

Start:

```json
{
	"objective": "Identify emergent bilingual semantic clusters",
	"max_iterations": 3
}
```
Step:

```json
{
	"iteration": 1,
	"max_new_docs": 10
}
```
Status (GET):

```json
{
	"iteration": 1,
	"novelty_mean": 0.34,
	"candidate_docs": ["swow_pt_12", "swow_es_88"],
	"accepted": ["swow_pt_12"],
	"rejected": []
}
```
Stop (POST) — corpo pode ser vazio.

## 5. Códigos de Erro

| Código | Motivo |
|--------|--------|
| 400 | Payload inválido / campo ausente |
| 401 | Falha de autenticação |
| 404 | Endpoint discovery desabilitado |
| 429 | Limite de requisições (externo/gateway) |
| 500 | Erro interno inesperado |

## 6. Exemplos curl

Iterative:

```bash
curl -s -X POST "$DARWIN_API_BASE/rag-plus/iterative" \
 -H "Authorization: Bearer $DARWIN_API_KEY" \
 -H "Content-Type: application/json" \
 -d '{"query":"Relate EEG entropy to SWOW lexical diversity","max_steps":3}'
```
Discovery status:

```bash
curl -s -X GET "$DARWIN_API_BASE/rag-plus/discovery/status" \
 -H "Authorization: Bearer $DARWIN_API_KEY"
```

## 7. Considerações de Performance

- Ajustar `top_k` e `max_steps` para controlar custo de embeddings/geração
- Uso de Vertex AI apenas quando variáveis setadas; fallback local possível (não parte desta release)

## 8. Observabilidade (Planejado)

| Métrica | Origem | Status |
|---------|--------|--------|
| `latency_ms` | Timer interno | ✅ |
| `steps_count` | Iterative loop | ✅ |
| `novelty_mean` | Discovery cálculo | ✅ |
| `token_usage` | Provider LLM | Planejado |
| `error_rate` | Logs agregados | Planejado |

## 9. Segurança

- Todas as rotas exigem API key
- Recomenda-se TLS (ver script run_ragpp_https.sh)
- Nenhum dado sensível armazenado em respostas

## 10. Limitações / Futuros

- Ausência de streaming de passos iterative
- Falta persistência histórica complete discovery
- Sem rate limiting nativo (usar gateway)

---
Darwin API v5.0 — Especificação inicial.
