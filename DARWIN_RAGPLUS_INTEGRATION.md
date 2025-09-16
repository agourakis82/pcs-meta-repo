# Darwin Platform - RAG++ Integration

## Overview

The **RAG++ Enhanced Research Agent** has been fully integrated into the Darwin Platform, providing advanced retrieval-augmented generation capabilities with long-horizon reasoning and scientific discovery monitoring.

## Features

### 🔍 Advanced Query Processing
- **Simple RAG**: Fast semantic search with answer generation
- **Iterative Reasoning**: Multi-step ReAct framework for complex questions
- **Scientific Discovery**: Automated monitoring of research literature

### 🧠 Long-Horizon Reasoning
- **Thought→Action→Observation loops**: Systematic problem decomposition
- **Configurable iterations**: Up to 5 reasoning steps per query
- **Context preservation**: Maintains conversation state across reasoning steps

### 📚 Knowledge Base Management
- **Vector embeddings**: Google Cloud BigQuery with vector search
- **Automatic indexing**: RSS feeds from arXiv, Nature, ScienceDaily
- **Novelty detection**: Similarity-based filtering for new discoveries

## API Endpoints

All endpoints are available under `/rag-plus` prefix:

### Query Endpoints

#### Simple Query
```http
POST /rag-plus/query
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "query": "What are the latest developments in transformer architectures?",
  "top_k": 10,
  "include_sources": true
}
```

#### Iterative Reasoning
```http
POST /rag-plus/iterative
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "query": "Compare the computational complexity of different attention mechanisms and recommend the most efficient for large language models",
  "include_sources": true
}
```

### Discovery Endpoints

#### Trigger Discovery Update
```http
POST /rag-plus/discovery
Authorization: Bearer YOUR_API_KEY
```

#### Continuous Discovery Management
```http
POST /rag-plus/discovery/start
POST /rag-plus/discovery/stop
```

### Management Endpoints

#### Service Status
```http
GET /rag-plus/status
Authorization: Bearer YOUR_API_KEY
```

#### Configuration
```http
GET /rag-plus/config
Authorization: Bearer YOUR_API_KEY
```

#### Knowledge Base Search
```http
GET /rag-plus/search?query=quantum computing&top_k=5
Authorization: Bearer YOUR_API_KEY
```

## Configuration

The RAG++ system is configured through environment variables in the Darwin Platform:

### Required Configuration

```bash
# BigQuery Configuration
RAG_PLUS_PROJECT_ID=your-gcp-project
RAG_PLUS_DATASET_ID=rag_plus_kb
RAG_PLUS_TABLE_ID=knowledge_base

# Model Configuration
RAG_PLUS_EMBEDDING_MODEL=textembedding-gecko@003
RAG_PLUS_GENERATION_MODEL=text-bison@002

# Discovery Configuration
RAG_PLUS_DISCOVERY_ENABLED=true
RAG_PLUS_RSS_FEEDS=arxiv_cs,nature,sciencedaily
RAG_PLUS_DISCOVERY_INTERVAL=3600
```

### Optional Configuration

```bash
# Reasoning Parameters
RAG_PLUS_MAX_ITERATIONS=5
RAG_PLUS_TOP_K_RETRIEVAL=10
RAG_PLUS_NOVELTY_THRESHOLD=0.8

# Feature Toggles
RAG_PLUS_ENABLED=true
```

## Setup Instructions

### 1. Google Cloud Setup

```bash
# Create BigQuery dataset and table
bq mk --dataset --location=us-central1 your-project:rag_plus_kb

bq mk --table \
  your-project:rag_plus_kb.knowledge_base \
  id:STRING,content:STRING,embedding:ARRAY<FLOAT64>,source:STRING,metadata:JSON,timestamp:TIMESTAMP
```

### 2. Environment Configuration

Set the required environment variables in your deployment environment:

```bash
export RAG_PLUS_PROJECT_ID="your-gcp-project"
export RAG_PLUS_DATASET_ID="rag_plus_kb"
export RAG_PLUS_TABLE_ID="knowledge_base"
export RAG_PLUS_DISCOVERY_ENABLED="true"
```

### 3. Darwin Platform Deployment

The RAG++ integration is automatically included when deploying Darwin Platform:

```bash
# Install dependencies
pip install -r requirements-darwin.txt

# Run the Darwin Platform
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Usage Examples

### Python Client Example

```python
import httpx
import asyncio

async def query_ragplus():
    async with httpx.AsyncClient() as client:
        # Simple query
        response = await client.post(
            "http://localhost:8000/rag-plus/query",
            json={
                "query": "Explain quantum entanglement in simple terms",
                "include_sources": True
            },
            headers={"Authorization": "Bearer YOUR_API_KEY"}
        )
        result = response.json()
        print(f"Answer: {result['answer']}")
        print(f"Sources: {len(result['sources'])}")

# Run the example
asyncio.run(query_ragplus())
```

### curl Examples

```bash
# Simple query
curl -X POST "http://localhost:8000/rag-plus/query" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "include_sources": true
  }'

# Iterative reasoning
curl -X POST "http://localhost:8000/rag-plus/iterative" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Design a neural network architecture for time series forecasting"
  }'

# Trigger discovery
curl -X POST "http://localhost:8000/rag-plus/discovery" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Check service status
curl "http://localhost:8000/rag-plus/status" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Response Formats

### Query Response
```json
{
  "answer": "Generated answer text with citations [1][2]",
  "sources": [
    {
      "id": "doc123",
      "content": "Source document content...",
      "source": "https://arxiv.org/abs/2023.12345",
      "similarity": 0.95,
      "metadata": {"title": "Paper Title", "authors": ["Author 1"]}
    }
  ],
  "method": "simple_rag",
  "retrieved_docs": 5,
  "reasoning_steps": null,
  "total_steps": null
}
```

### Iterative Response
```json
{
  "answer": "Final reasoned answer",
  "sources": [...],
  "method": "iterative_reasoning",
  "retrieved_docs": 15,
  "reasoning_steps": [
    {
      "step": 1,
      "thought": "I need to break down this complex question...",
      "action": "search",
      "query": "neural network architectures",
      "observation": "Found 10 relevant papers about..."
    }
  ],
  "total_steps": 3
}
```

### Discovery Response
```json
{
  "status": "completed",
  "fetched": 25,
  "novel": 8,
  "added": 8,
  "errors": 0
}
```

## Monitoring and Debugging

### Health Checks

```bash
# Quick health check
curl "http://localhost:8000/rag-plus/health"

# Detailed status
curl "http://localhost:8000/rag-plus/status" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Log Monitoring

The RAG++ service logs important events:

```bash
# Service startup
INFO:rag_plus_service:RAG++ service initialized
INFO:rag_plus_service:BigQuery connection established
INFO:rag_plus_service:Discovery monitoring started

# Query processing
INFO:rag_plus_router:RAG++ query: What is quantum computing...
INFO:rag_plus_service:Retrieved 8 documents, similarity > 0.7
INFO:rag_plus_service:Generated answer in 2.3s

# Discovery events
INFO:discovery_radar:Fetched 15 new articles from arXiv
INFO:discovery_radar:Found 3 novel articles, added to knowledge base
```

## Error Handling

### Common Errors

1. **BigQuery Connection Error**
   ```json
   {"detail": "BigQuery connection failed: Project not found"}
   ```
   *Solution*: Verify `RAG_PLUS_PROJECT_ID` and GCP credentials

2. **Model Access Error**
   ```json
   {"detail": "Vertex AI access denied"}
   ```
   *Solution*: Check Vertex AI API permissions and quotas

3. **Discovery Source Error**
   ```json
   {"detail": "RSS feed unavailable: arxiv.org"}
   ```
   *Solution*: Check network connectivity and feed URLs

### Rate Limiting

RAG++ endpoints respect Darwin Platform rate limits:
- 60 requests per minute per API key
- Iterative queries count as 1 request regardless of reasoning steps
- Discovery operations have extended timeouts (5 minutes)

## Performance Optimization

### Query Performance
- **Simple queries**: ~1-3 seconds
- **Iterative queries**: ~5-15 seconds (depending on complexity)
- **Discovery updates**: ~30-120 seconds

### Caching
- Embedding cache: 1 hour TTL
- Query results cache: 30 minutes TTL
- Knowledge base updates: Real-time

### Scaling Considerations
- BigQuery handles up to 1M+ documents efficiently
- Vertex AI models support concurrent requests
- Discovery monitoring scales with RSS feed count

## Integration Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Darwin API    │────│  RAG++ Service   │────│   BigQuery KB   │
│   (FastAPI)     │    │  (DarwinRAGPlus) │    │  (Vector Store) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐             │
         │──────────────│  Vertex AI       │─────────────│
         │              │  (Embeddings +   │             │
         │              │   Generation)    │             │
         │              └──────────────────┘             │
         │                       │                       │
         │              ┌──────────────────┐             │
         └──────────────│  Discovery Radar │─────────────┘
                        │  (RSS Monitoring)│
                        └──────────────────┘
```

## Security Considerations

- **API Authentication**: All endpoints require valid API key
- **GCP Permissions**: Minimal required permissions for BigQuery and Vertex AI
- **Data Privacy**: No persistent storage of user queries
- **Rate Limiting**: Protection against abuse and resource exhaustion

## Troubleshooting

### Service Not Starting
1. Check environment variables are set correctly
2. Verify GCP credentials and permissions
3. Ensure BigQuery dataset/table exists
4. Check Vertex AI API quotas

### Poor Query Results
1. Verify knowledge base has sufficient content
2. Check embedding model performance
3. Adjust `RAG_PLUS_TOP_K_RETRIEVAL` parameter
4. Review `RAG_PLUS_NOVELTY_THRESHOLD` setting

### Discovery Not Working
1. Check RSS feed URLs are accessible
2. Verify discovery interval configuration
3. Monitor discovery service logs
4. Test manual discovery trigger

## Support

For issues and support:
1. Check service status: `GET /rag-plus/status`
2. Review application logs
3. Verify configuration parameters
4. Test individual components (BigQuery, Vertex AI, RSS feeds)

## Version History

- **v1.0.0**: Initial RAG++ integration with Darwin Platform
- Full iterative reasoning with ReAct framework
- Scientific discovery monitoring
- Complete Darwin Platform integration

---

*RAG++ Enhanced Research Agent - Integrated with Darwin Platform*