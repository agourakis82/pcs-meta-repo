RAG++ Environment Variables
Summary of the most relevant environment variables to configure the RAG++ server, memory, caching and bridges.

Server & Runtime
- RAG_HOST: Bind host for FastAPI (default: 0.0.0.0)
- RAG_PORT: Bind port for FastAPI (default: 8000)
- RAG_WORKERS: Number of uvicorn workers (default: 4)
- RAG_RELOAD: Auto-reload in dev (0/1)
- USE_UVLOOP: Use uvloop event loop (1 default)
- USE_HTTPTOOLS: Use httptools HTTP parser (1 default)
- PRODUCTION: Disable access log when 1

Security
- RAG_API_TOKEN: Bearer token for protected routes (e.g., store context)
- MCP_BEARER_TOKEN: Bearer for MCP over HTTP/SSE endpoint
- MCP_ALLOWED_HOSTS: Comma-separated host allowlist for MCP endpoint
- RAG_JSON_LOGS: When 1, emit structured JSON logs

Actions/Plugins
- ACTIONS_AUTH_MODE: Controls Actions schema security hints (none/bearer)

MCP/Gemini Bridges
- GEMINI_API_KEY: Google Generative Language API key
- GEMINI_MODEL: Gemini model (default: gemini-1.5-pro)
- RAGPP_BASE_URL: Base URL for RAG++ REST when using the Gemini bridge
- BRIDGE_AUTO_STORE: If 1, auto-store conversation after the final answer

LLM Deterministic Cache
- ENABLE_LM_CACHE: Enable deterministic LM cache (default: 1)
- NO_LM_CACHE: Disable cache (default: 0)
- LM_CACHE_TTL_SECONDS: Cache TTL in seconds (default: 86400)
- LM_CACHE_PATH: SQLite path for cache (default: ragpp/data/lm_cache.db)

Semantic Cache (Near-Duplicate)
- SEM_CACHE_THRESHOLD: Cosine similarity threshold (default: 0.97)
- SEM_CACHE_PATH: Chroma path (default: ragpp/data/lm_semantic_cache)

Extended Memory Service
- MEM_ENCRYPTION_KEY: Fernet key to encrypt content at rest (optional)
- MEM_CLEANUP_INTERVAL_SECONDS: Background cleanup interval (0 to disable)
- MEM_RETENTION_DAYS: Remove old, low-importance memories after N days (default: 90)

Notes
- To generate a Fernet key: python scripts/generate_fernet_key.py
- Expose metrics for monitoring at /metrics (text exposition; latency p50/p95/p99).
  If prometheus_client is installed, /metrics returns native Prometheus format with default counters/histogram.
