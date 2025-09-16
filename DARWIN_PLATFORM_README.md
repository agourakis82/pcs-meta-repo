# Darwin Platform

> Advanced RAG + Tree-Search platform with Vertex AI integration, project memory, and context caching.

## 🌟 Overview

Darwin is a comprehensive platform that combines:
- **Vertex-native RAG**: Multiple backends (RAG Engine + Vector Search)
- **Project Memory**: JSONL + SQLite hybrid storage with RAG-powered search
- **Tree-Search PUCT**: Monte Carlo Tree Search with Polynomial Upper Confidence Bounds
- **Score Contracts**: Sandboxed execution environment for specialized scoring
- **Context Caching**: Intelligent prompt optimization for Gemini models
- **Security**: API key authentication with token bucket rate limiting

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Project with Vertex AI enabled
- API keys configured

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install test dependencies (optional)
pip install -r test-requirements.txt

# Set environment variables
export PROJECT_ID="your-gcp-project"
export LOCATION="us-central1"
export BASE_URL="https://your-app.run.app"
export OPENAI_VERIFICATION_TOKEN="your-token"
```

### Running the Platform

```bash
# Start the Darwin platform
uvicorn main:app --host 0.0.0.0 --port 8000

# With auto-reload for development
uvicorn main:app --reload
```

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **ChatGPT Actions**: http://localhost:8000/.well-known/ai-plugin.json
- **Gemini Extensions**: http://localhost:8000/.well-known/gemini-extension.json

## 🏗️ Architecture

### Core Services

```
services/
├── settings.py          # Darwin platform configuration
├── rag_vertex.py        # Vertex AI RAG backends
├── tree_search.py       # PUCT tree search algorithms
├── score_contracts.py   # Sandboxed contract execution
└── context_cache.py     # Context caching for Gemini
```

### API Routers

```
api/routers/
├── rag.py              # RAG query endpoints
├── memory.py           # Project memory & search
├── tree_search.py      # Tree exploration endpoints
├── score_contracts.py  # Contract execution endpoints
├── context_cache.py    # Cache management endpoints
└── health.py           # Health & monitoring
```

### Security Layer

```
api/
├── security.py         # API key auth + rate limiting
└── openapi_config.py   # ChatGPT Actions integration
```

## 📚 API Reference

### RAG Endpoints

```bash
# Query with RAG
POST /rag
{
  "query": "Your question here",
  "max_results": 5,
  "include_citations": true
}

# Retrieve documents
GET /rag/retrieve?query=search_term&limit=10
```

### Tree Search

```bash
# Full tree search
POST /tree-search/search
{
  "initial_state": "start",
  "num_simulations": 100,
  "max_depth": 5,
  "c_puct": 1.414
}

# Quick exploration
POST /tree-search/quick-search
{
  "state": "current_position",
  "depth": 3
}
```

### Score Contracts

```bash
# Execute contract
POST /score-contracts/execute
{
  "contract_type": "delta_kec_v1",
  "data": {
    "knowledge_vectors": [...],
    "interaction_weight": 0.7
  }
}

# Batch execution
POST /score-contracts/batch-execute
{
  "contracts": [
    {"type": "delta_kec_v1", "data": {...}},
    {"type": "zuco_reading_v1", "data": {...}}
  ]
}
```

### Context Caching

```bash
# Analyze prompt for caching
POST /context-cache/analyze
{
  "prompt": "You are an expert...",
  "model": "gemini-1.5-pro"
}

# Optimize prompt
POST /context-cache/optimize
{
  "prompt": "Your full prompt here",
  "model": "gemini-1.5-pro"
}
```

### Project Memory

```bash
# Log session
POST /memory/session/log
{
  "session_id": "unique-session",
  "query": "User question",
  "response": "Assistant response",
  "metadata": {}
}

# Search sessions
GET /memory/search?query=search_term&session_id=optional
```

## 🧪 Testing

### Run Test Suite

```bash
# All tests
pytest

# Specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests

# With coverage
pytest --cov=services --cov=api --cov-report=html
```

### Test Structure

```
tests/
└── test_darwin_platform.py  # Comprehensive test suite
    ├── TestDarwinSettings   # Configuration tests
    ├── TestVertexRagBackends # RAG backend tests
    ├── TestSecurity         # Auth & rate limiting
    ├── TestMemoryStorage    # Memory & search tests
    ├── TestTreeSearch       # PUCT algorithm tests
    ├── TestScoreContracts   # Contract execution tests
    ├── TestContextCache     # Cache system tests
    └── TestIntegration      # End-to-end tests
```

## 🔧 Configuration

### Environment Variables

```bash
# Core settings
PROJECT_ID=your-gcp-project
LOCATION=us-central1
BASE_URL=https://your-app.run.app

# RAG configuration
RAG_ENGINE_ENABLED=true
RAG_ENGINE_ID=your-rag-engine
VECTOR_SEARCH_ENABLED=true
VECTOR_INDEX_ENDPOINT=your-vector-endpoint

# Security
API_KEYS=key1,key2,key3
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# External integrations
OPENAI_VERIFICATION_TOKEN=your-token
CONTEXT_CACHE_ENABLED=true

# Memory storage
MEMORY_STORAGE_DIR=/tmp/darwin-memory
```

### Pydantic Settings

The platform uses Pydantic BaseSettings for configuration with:
- Environment variable override
- Google Cloud Secret Manager integration
- Type validation and conversion
- Default values for all settings

## 🚢 Deployment

### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy darwin-platform \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

### Docker

```bash
# Build image
docker build -t darwin-platform .

# Run locally
docker run -p 8000:8000 \
  -e PROJECT_ID=your-project \
  -e LOCATION=us-central1 \
  darwin-platform
```

### Railway

```bash
# Deploy to Railway
railway login
railway link
railway up
```

## 🎯 Features

### RAG Backends

- **RAG Engine**: Vertex AI RAG with built-in grounding
- **Vector Search**: Custom vector similarity search
- **Caching**: LRU cache for frequent queries
- **Health Checks**: Backend availability monitoring

### Tree Search

- **PUCT Algorithm**: Polynomial Upper Confidence Bounds for Trees
- **Monte Carlo**: Selection, expansion, simulation, backpropagation
- **Configurable**: Adjustable exploration parameters
- **State Evaluation**: Pluggable state evaluator interface

### Score Contracts

- **Delta KEC v1**: Knowledge Exchange Coefficient scoring
- **ZuCo Reading v1**: EEG + eye-tracking cognitive load analysis
- **Editorial v1**: Text quality and readability scoring
- **Sandboxed**: Timeout protection and error handling

### Context Caching

- **Prefix Detection**: Automatic stable prefix identification
- **Cache Management**: LRU eviction and statistics
- **Optimization**: Performance savings estimation
- **Gemini Integration**: Context caching for Gemini prompts

### Security

- **API Key Auth**: Multi-key authentication support
- **Rate Limiting**: Token bucket with per-key limits
- **CORS**: Configurable cross-origin policies
- **Headers**: Security and caching headers

## 📊 Monitoring

### Health Endpoints

```bash
GET /health      # Overall system health
GET /ping        # Simple connectivity check
GET /ready       # Readiness probe
GET /live        # Liveness probe
GET /version     # Version information
```

### Metrics

- RAG backend response times
- Cache hit ratios
- Rate limiting statistics
- Tree search performance
- Contract execution times

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd pcs-meta-repo

# Install dependencies
pip install -r requirements.txt
pip install -r test-requirements.txt

# Run tests
pytest

# Run linting
flake8 .
black --check .
isort --check-only .
```

### Code Style

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **Type hints**: Full type annotation coverage
- **Docstrings**: Comprehensive documentation

## 📄 License

See LICENSE file for details.

## 🔗 Related Projects

- [Vertex AI](https://cloud.google.com/vertex-ai)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)

---

**Darwin Platform** - Advanced RAG + Tree-Search platform for intelligent applications.