#!/usr/bin/env python3
"""
RAG++ Web Server - MCP via HTTPS
Servidor web para expor o sistema RAG++ como API REST acessível pelo ChatGPT web.
"""

import asyncio
import json
import logging
import multiprocessing
import os
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Web framework imports
try:
    import uvicorn
    from fastapi import Depends, FastAPI, HTTPException, Request, Response, Security
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    from pydantic import BaseModel
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("pip install fastapi uvicorn python-multipart")
    sys.exit(1)

# MCP HTTP transport (for ChatGPT Connector)
try:
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
except Exception as e:
    # Optional: MCP HTTP transport is only needed for the /mcp endpoint
    StreamableHTTPSessionManager = None  # type: ignore

# Optional Prometheus metrics
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Histogram,
        generate_latest,
    )

    _prom_registry = CollectorRegistry()
    _prom_requests = Counter(
        "ragpp_requests_total",
        "Requests total",
        ["route"],
        registry=_prom_registry,
    )
    _prom_errors = Counter(
        "ragpp_errors_total",
        "Errors total",
        ["route"],
        registry=_prom_registry,
    )
    _prom_latency = Histogram(
        "ragpp_requests_latency_ms",
        "Request latency in milliseconds",
        ["route"],
        buckets=(1, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000),
        registry=_prom_registry,
    )
    _PROM_AVAILABLE = True
except Exception:
    _PROM_AVAILABLE = False

# Add current directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from ragpp.cache_manager import get_cache, init_cache
    from ragpp.extended_memory_service import ExtendedMemoryService, get_memory_service
    from ragpp.tools.mcp_rag_integration import MCPRAGIntegration
    from ragpp.tree_search_optimized import (
        NodeType,
        SearchStrategy,
        TreeFactory,
        TreeNode,
        TreeSearchEngine,
    )
except ImportError:
    try:
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from ragpp.cache_manager import get_cache, init_cache
        from ragpp.extended_memory_service import (
            ExtendedMemoryService,
            get_memory_service,
        )
        from ragpp.tools.mcp_rag_integration import MCPRAGIntegration
        from ragpp.tree_search_optimized import (
            NodeType,
            SearchStrategy,
            TreeFactory,
            TreeNode,
            TreeSearchEngine,
        )
    except ImportError:
        print(
            "❌ Could not import MCPRAGIntegration, ExtendedMemoryService, or TreeSearch. Check paths."
        )
        sys.exit(1)


class SimpleJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        from datetime import datetime as _dt

        payload = {
            "ts": _dt.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _setup_logging():
    logging.basicConfig(level=logging.INFO)
    if os.getenv("RAG_JSON_LOGS", "0").strip().lower() in ("1", "true", "yes"):
        fmt = SimpleJSONFormatter()
        root = logging.getLogger()
        for h in root.handlers:
            try:
                h.setFormatter(fmt)
            except Exception:
                pass


_setup_logging()
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)


# API Models
class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10
    include_sources: Optional[bool] = True
    search_type: Optional[str] = "hybrid"  # hybrid, literature, memory, live_literature


class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    sources: Dict[str, int]
    confidence: float
    timestamp: str


class ResearchRequest(BaseModel):
    content: str
    category: Optional[str] = "research_findings"
    tags: Optional[List[str]] = None
    importance: Optional[int] = 3


class HealthResponse(BaseModel):
    status: str
    version: str
    capabilities: List[str]
    indexed_articles: int
    timestamp: str


# Prepare MCP server (RAG++ over MCP) if library available
MCP_SESSION_MANAGER = None
MCP_APP = None
try:
    # Import our MCP stdio server implementation and reuse its Server instance
    from ragpp.ragpp_mcp_server import RAGPlusMCPServer  # type: ignore

    _mcp_instance = RAGPlusMCPServer()
    if StreamableHTTPSessionManager:
        MCP_SESSION_MANAGER = StreamableHTTPSessionManager(_mcp_instance.server)

        class MCPASGIApp:
            def __init__(self, manager: StreamableHTTPSessionManager):  # type: ignore
                self.manager = manager

            async def __call__(self, scope, receive, send):
                await self.manager.handle_request(scope, receive, send)

        MCP_APP = MCPASGIApp(MCP_SESSION_MANAGER)
except Exception as _e:
    # If anything fails, keep REST API operational; /mcp will be unavailable
    MCP_SESSION_MANAGER = None
    MCP_APP = None

from contextlib import asynccontextmanager

# Global variables
rag_system: Optional[MCPRAGIntegration] = None
cache_system = None
tree_search_engine: Optional["TreeSearchEngine"] = None


@asynccontextmanager
async def lifespan(app):
    global rag_system, cache_system, tree_search_engine
    try:
        logger.info("🔧 Initializing RAG++ system...")
        rag_system = MCPRAGIntegration()
        logger.info("✅ RAG++ system initialized successfully")

        logger.info("🗄️ Initializing cache system...")
        if "get_cache" in globals():
            cache_system = get_cache()
            logger.info("✅ Cache system initialized successfully")
        else:
            logger.warning("⚠️ Cache system not available (get_cache not imported)")
            cache_system = None

        # Initialize tree search engine
        logger.info("🌳 Initializing tree search system...")
        from ragpp.tree_search_optimized import TreeFactory

        tree_search_engine = TreeFactory.create_research_tree()
        logger.info("✅ Tree search system initialized successfully")

    except Exception as e:
        logger.exception(f"❌ Failed to initialize systems: {e}")
        rag_system = None
        cache_system = None
        tree_search_engine = None

    if MCP_SESSION_MANAGER is not None:
        async with MCP_SESSION_MANAGER.run():
            yield
    else:
        yield


# Initialize FastAPI app
app = FastAPI(
    title="RAG++ Research API",
    description=(
        "Scientific Research Assistant with recent literature and project " "knowledge"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration for ChatGPT web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chat.openai.com", "https://chatgpt.com", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Global RAG system instance
rag_system: Optional[MCPRAGIntegration] = None
cache_system = None
last_init_error: Optional[str] = None

# Simple in-process metrics (JSON and Prometheus exposition)
_metrics = {
    "requests_total": {},  # per route
    "errors_total": {},  # per route
    "last_request_ts": {},
}

# Rolling latency samples per route (milliseconds)
_latency_samples: Dict[str, deque] = defaultdict(lambda: deque(maxlen=512))


def _bump_metric(bucket: Dict[str, int], key: str, inc: int = 1):
    bucket[key] = int(bucket.get(key, 0)) + inc


def _mark_request(route: str):
    _bump_metric(_metrics["requests_total"], route)
    _metrics["last_request_ts"][route] = datetime.now().isoformat()
    try:
        if _PROM_AVAILABLE:
            _prom_requests.labels(route=route).inc()
    except Exception:
        pass


def _mark_error(route: str):
    _bump_metric(_metrics["errors_total"], route)
    try:
        if _PROM_AVAILABLE:
            _prom_errors.labels(route=route).inc()
    except Exception:
        pass


@app.middleware("http")
async def _latency_middleware(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
        return response
    finally:
        duration_ms = (time.perf_counter() - start) * 1000.0
        path = request.url.path
        try:
            _latency_samples[path].append(duration_ms)
            if _PROM_AVAILABLE:
                _prom_latency.labels(route=path).observe(duration_ms)
        except Exception:
            pass


init_lock: Optional[asyncio.Lock] = None


async def ensure_initialized() -> bool:
    global rag_system, cache_system, last_init_error, init_lock
    if rag_system is not None:
        return True
    # Create per-process lock lazily
    if init_lock is None:
        init_lock = asyncio.Lock()
    async with init_lock:  # type: ignore
        if rag_system is not None:
            return True
        try:
            logger.info("🔧 Lazy-initializing RAG++ system (on-demand)...")
            rag_system = MCPRAGIntegration()
            logger.info("✅ RAG++ system initialized (lazy)")

            logger.info("🗄️ Lazy-initializing cache system...")
            if "get_cache" in globals():
                cache_system = get_cache()
                logger.info("✅ Cache system initialized (lazy)")
            else:
                logger.warning("⚠️ Cache system not available (get_cache not imported)")
                cache_system = None
            last_init_error = None
            return True
        except Exception as e:
            last_init_error = str(e)
            rag_system = None
            cache_system = None
            logger.exception("❌ Lazy initialization failed: %s", last_init_error)
            return False


# API Key validation (optional)
def get_verify_token_dependency():
    """Get the appropriate token verification dependency based on configuration."""
    expected_token = os.getenv("RAG_API_TOKEN")
    if expected_token:
        # Token configured - require authentication
        def verify_token_with_auth(
            credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
        ):
            if not credentials or credentials.credentials != expected_token:
                raise HTTPException(
                    status_code=401, detail="Invalid authentication token"
                )
            return credentials.credentials

        return verify_token_with_auth
    else:
        # No token configured - no dependency needed
        return None


# Get the appropriate dependency
verify_token_dependency = get_verify_token_dependency()


# Mount MCP over HTTP endpoint for ChatGPT Connector (SSE + JSON-RPC)
if MCP_APP is not None:
    # Optional security wrapper: Bearer token + host allowlist
    class MCPProtectedApp:
        def __init__(
            self,
            inner_app,
            token: str | None = None,
            allowed_hosts: list[str] | None = None,
        ):
            self.inner_app = inner_app
            self.token = token
            self.allowed_hosts = [
                h.strip().lower() for h in (allowed_hosts or []) if h.strip()
            ]

        async def __call__(self, scope, receive, send):
            if scope.get("type") != "http":
                return await self.inner_app(scope, receive, send)

            # Extract headers
            headers = {
                k.decode("latin1").lower(): v.decode("latin1")
                for k, v in scope.get("headers", [])
            }

            # Enforce host allowlist if provided
            if self.allowed_hosts:
                host = headers.get("host", "").split(":")[0].lower()
                if host not in self.allowed_hosts:
                    resp = JSONResponse({"error": "Forbidden host"}, status_code=403)
                    return await resp(scope, receive, send)

            # Enforce Bearer token if configured
            if self.token:
                auth = headers.get("authorization", "")
                if (
                    not auth.startswith("Bearer ")
                    or auth.split(" ", 1)[1] != self.token
                ):
                    # Allow preflight
                    if scope.get("method") == "OPTIONS":
                        resp = JSONResponse({}, status_code=204)
                        return await resp(scope, receive, send)
                    resp = JSONResponse({"error": "Unauthorized"}, status_code=401)
                    return await resp(scope, receive, send)

            return await self.inner_app(scope, receive, send)

    _mcp_token = os.getenv("MCP_BEARER_TOKEN")
    _allowed_hosts_env = os.getenv("MCP_ALLOWED_HOSTS", "")
    _allowed_hosts = [h for h in _allowed_hosts_env.split(",") if h.strip()]

    protected_app = MCPProtectedApp(
        MCP_APP, token=_mcp_token, allowed_hosts=_allowed_hosts
    )
    app.mount("/mcp", protected_app)
    # Alias commonly expected by ChatGPT connector docs
    app.mount("/sse", protected_app)
    app.mount("/sse/", protected_app)
    logger.info(
        "✅ MCP HTTP endpoint mounted at /mcp (auth=%s, hosts=%s)",
        "on" if _mcp_token else "off",
        ",".join(_allowed_hosts) or "*",
    )
else:
    logger.warning(
        "ℹ️ MCP HTTP endpoint not available (model-context-protocol HTTP "
        "transport missing)"
    )


@app.get("/", response_model=HealthResponse)
async def root():
    _mark_request("/")
    """Health check and system information."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        capabilities=[
            "hybrid_search",
            "literature_search",
            "memory_search",
            "research_storage",
            "knowledge_synthesis",
        ],
        indexed_articles=168,  # From previous collection
        timestamp=datetime.now().isoformat(),
    )


# Explicit HEAD handlers to avoid 405 on health/root checks
@app.head("/")
async def root_head():
    return Response(status_code=200)


@app.head("/health")
async def health_head():
    return Response(status_code=200)


@app.get("/health", response_model=HealthResponse)
async def health():
    _mark_request("/health")
    """Explicit health endpoint for external checks."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        capabilities=[
            "hybrid_search",
            "literature_search",
            "memory_search",
            "research_storage",
            "knowledge_synthesis",
        ],
        indexed_articles=168,
        timestamp=datetime.now().isoformat(),
    )


@app.get("/test")
async def test_endpoint():
    _mark_request("/test")
    """Simple test endpoint."""
    return {"message": "Test endpoint working", "timestamp": datetime.now().isoformat()}


@app.post("/search", response_model=SearchResponse)
async def search_research(request: SearchRequest):
    _mark_request("/search")
    """
    Search research literature and project knowledge.

    This endpoint provides access to recent scientific literature (2020-2025)
    and project-specific knowledge through a hybrid RAG++ system.
    """
    ok = await ensure_initialized()
    if not ok or not rag_system:
        msg = "RAG system not initialized"
        if last_init_error:
            msg += f": {last_init_error}"
        raise HTTPException(status_code=503, detail=msg)

    try:
        # Try cache first
        cached_result = None
        if cache_system:
            search_type = request.search_type or "hybrid"
            max_results = request.max_results or 10
            cached_result = cache_system.get(request.query, search_type, max_results)
            if cached_result:
                logger.info(f"🚀 Cache hit for query: {request.query[:50]}...")
                return SearchResponse(**cached_result)

        # Perform search based on type
        search_type = request.search_type or "hybrid"
        max_results = request.max_results or 10

        if search_type == "hybrid":
            response = rag_system.hybrid_search(
                query=request.query,
                max_rag_results=max_results,
                max_mcp_results=max_results,
                search_type="hybrid",
            )
        elif search_type == "literature":
            response = rag_system.hybrid_search(
                query=request.query,
                max_rag_results=max_results,
                max_mcp_results=0,
                search_type="hybrid",
            )
        elif search_type == "memory":
            response = rag_system.hybrid_search(
                query=request.query,
                max_rag_results=0,
                max_mcp_results=max_results,
                search_type="hybrid",
            )
        elif search_type == "live_literature":
            response = rag_system.hybrid_search(
                query=request.query,
                max_rag_results=0,
                max_mcp_results=0,
                search_type="live_literature",
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid search_type")

        # Format results
        results = []

        # Add literature results
        if "literature_results" in response:
            for result in response["literature_results"]:
                results.append(
                    {
                        "type": "literature",
                        "title": result.get("title", "Unknown"),
                        "authors": result.get("authors", "Unknown"),
                        "content": result.get("content", ""),
                        "journal": result.get("journal", ""),
                        "year": result.get("year", ""),
                        "relevance_score": result.get("score", 0),
                    }
                )

        # Add RAG results (literature or live_literature)
        if "rag_results" in response:
            for result in response["rag_results"]:
                item = {
                    "type": "literature",
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "relevance_score": result.get("score", 0),
                }
                meta = item["metadata"]
                # Flatten common fields if present
                if isinstance(meta, dict):
                    if meta.get("title"):
                        item["title"] = meta.get("title")
                    if meta.get("authors"):
                        item["authors"] = meta.get("authors")
                    if meta.get("journal"):
                        item["journal"] = meta.get("journal")
                    if meta.get("year"):
                        item["year"] = meta.get("year")
                    if meta.get("pmid"):
                        item["pmid"] = meta.get("pmid")
                results.append(item)

        # Add memory results
        if "memory_results" in response:
            for result in response["memory_results"]:
                results.append(
                    {
                        "type": "memory",
                        "content": result.get("content", ""),
                        "category": result.get("category", "general"),
                        "tags": result.get("tags", []),
                        "importance": result.get("importance", 1),
                        "timestamp": result.get("timestamp", ""),
                    }
                )

        # Add MCP results if hybrid search
        if "mcp_results" in response:
            for result in response["mcp_results"]:
                results.append(
                    {
                        "type": "memory",
                        "content": result.get("content", ""),
                        "category": result.get("category", "general"),
                        "metadata": result.get("metadata", {}),
                    }
                )

        search_response = SearchResponse(
            query=request.query,
            results=results[:max_results],
            sources=response.get(
                "sources",
                {
                    "literature": 0,
                    "memory": 0,
                    "live_literature": 0,
                    "total": 0,
                },
            ),
            confidence=response.get("confidence", 0.0),
            timestamp=datetime.now().isoformat(),
        )

        # Cache the result
        if cache_system:
            cache_system.set(
                request.query,
                search_type,
                max_results,
                search_response.model_dump(),
                ttl=1800,  # 30 minutes cache
            )
            logger.info(f"💾 Cached result for query: {request.query[:50]}...")

        return search_response

    except Exception as e:
        logger.error(f"Search error: {e}")
        _mark_error("/search")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/research/store")
async def store_research(
    request: ResearchRequest, token: Optional[str] = Depends(verify_token_dependency)
):
    _mark_request("/research/store")
    """Store new research finding in the system."""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        success = rag_system.store_research_finding(
            content=request.content,
            category=request.category or "research_findings",
            tags=request.tags or [],
            importance=request.importance or 3,
            auto_index_to_rag=True,
        )

        if success:
            return {
                "status": "success",
                "message": "Research finding stored successfully",
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to store research finding"
            )

    except Exception as e:
        logger.error(f"Store error: {e}")
        _mark_error("/research/store")
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")


@app.get("/research/categories")
async def get_categories():
    _mark_request("/research/categories")
    """Get available research categories."""
    return {
        "categories": [
            "computational_methods",
            "therapeutic_insights",
            "research_findings",
            "neuroimaging_findings",
            "language_analysis",
            "general",
        ]
    }


@app.get("/cache/stats")
async def get_cache_stats():
    _mark_request("/cache/stats")
    """Retorna estatísticas do sistema de cache."""
    if not cache_system:
        return {"status": "cache_not_initialized"}

    try:
        stats = cache_system.get_stats()
        return {
            "status": "active",
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return {"status": "error", "message": str(e)}


# OpenAI Plugin Manifest for ChatGPT
@app.get("/.well-known/ai-plugin.json")
async def ai_plugin_manifest():
    _mark_request("/.well-known/ai-plugin.json")
    """OpenAI plugin manifest for ChatGPT integration."""
    return {
        "schema_version": "v1",
        "name_for_human": "RAG++ Scientific Research Assistant",
        "name_for_model": "ragpp_research",
        "description_for_human": (
            "Access recent scientific literature and research insights in psychiatry, "
            "computational methods, and neuroimaging."
        ),
        "description_for_model": (
            "This plugin provides access to recent scientific literature (2020-2025) "
            "and project-specific knowledge through a hybrid RAG++ system. Use it to "
            "enhance responses with current research findings, especially in "
            "psychiatry, "
            "computational methods, neuroimaging, and digital phenotyping. The system "
            "can search literature, access project memories, and provide "
            "synthesized insights."
        ),
        "auth": {"type": "bearer", "authorization_type": "bearer"},
        "api": {
            "type": "openapi",
            "url": f"{os.getenv('RAG_SERVER_URL', 'https://your-domain.com')}/openapi.json",
        },
        "logo_url": f"{os.getenv('RAG_SERVER_URL', 'https://your-domain.com')}/static/logo.png",
        "contact_email": "support@your-domain.com",
        "legal_info_url": f"{os.getenv('RAG_SERVER_URL', 'https://your-domain.com')}/legal",
    }


def _build_actions_schema(auth_mode: str, base_url: str) -> dict:
    base = {
        "openapi": "3.0.0",
        "info": {
            "title": "RAG++ Research API",
            "description": (
                "Scientific research assistant with recent literature access"
            ),
            "version": "1.0.0",
        },
        "servers": [{"url": base_url}],
        "paths": {
            "/health": {
                "get": {
                    "operationId": "checkServerHealth",
                    "summary": "Check server health/status",
                    "responses": {
                        "200": {
                            "description": "Server is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "version": {"type": "string"},
                                            "capabilities": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "indexed_articles": {"type": "integer"},
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/search": {
                "post": {
                    "operationId": "searchResearch",
                    "summary": (
                        "Search recent scientific literature and research knowledge"
                    ),
                    "description": (
                        "Search through recent scientific literature (2020-2025) and "
                        "project-specific research knowledge using hybrid RAG++ system."
                    ),
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "Research query or question",
                                        },
                                        "max_results": {
                                            "type": "integer",
                                            "default": 10,
                                            "description": "Maximum number of results",
                                        },
                                        "search_type": {
                                            "type": "string",
                                            "enum": [
                                                "hybrid",
                                                "literature",
                                                "memory",
                                                "live_literature",
                                            ],
                                            "default": "hybrid",
                                            "description": "Type of search to perform",
                                        },
                                    },
                                    "required": ["query"],
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Search results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {"type": "string"},
                                            "results": {
                                                "type": "array",
                                                "items": {"type": "object"},
                                            },
                                            "sources": {"type": "object"},
                                            "confidence": {"type": "number"},
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/research/recent": {
                "get": {
                    "operationId": "getRecentResearch",
                    "summary": "Get recent research findings",
                    "description": (
                        "Retrieve the most recent research findings and developments"
                    ),
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 10},
                            "description": "Number of recent findings to return",
                        }
                    ],
                    "responses": {"200": {"description": "Recent research findings"}},
                }
            },
            "/memory/chatgpt/context": {
                "post": {
                    "operationId": "storeChatGPTContext",
                    "summary": "Store conversation context and insights",
                    "description": (
                        "Persist ChatGPT conversation messages, summary and importance "
                        "into the Extended Memory Service for future recall."
                    ),
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "conversation_title": {"type": "string"},
                                        "messages": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "role": {"type": "string"},
                                                    "content": {"type": "string"},
                                                },
                                                "required": ["role", "content"],
                                            },
                                        },
                                        "context_summary": {"type": "string"},
                                        "importance_score": {
                                            "type": "number",
                                            "default": 0.7,
                                        },
                                    },
                                    "required": ["conversation_title", "messages"],
                                }
                            }
                        },
                    },
                    "responses": {"200": {"description": "Stored"}},
                }
            },
            "/memory/chatgpt/recall": {
                "get": {
                    "operationId": "recallChatGPTContext",
                    "summary": "Recall relevant project context",
                    "description": (
                        "Retrieve semantically relevant memories for a query from the "
                        "Extended Memory Service."
                    ),
                    "parameters": [
                        {
                            "name": "query",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "include_conversations",
                            "in": "query",
                            "schema": {"type": "boolean", "default": True},
                        },
                        {
                            "name": "include_insights",
                            "in": "query",
                            "schema": {"type": "boolean", "default": True},
                        },
                        {
                            "name": "max_results",
                            "in": "query",
                            "schema": {"type": "integer", "default": 10},
                        },
                    ],
                    "responses": {"200": {"description": "Relevant context"}},
                }
            },
        },
    }

    if auth_mode == "bearer":
        base.setdefault("components", {}).setdefault("securitySchemes", {})[
            "bearerAuth"
        ] = {"type": "http", "scheme": "bearer"}
        # Apply security to operations that need it
        base["paths"]["/search"]["post"]["security"] = [{"bearerAuth": []}]
        # Optionally protect memory writes
        if "/memory/chatgpt/context" in base["paths"]:
            base["paths"]["/memory/chatgpt/context"]["post"]["security"] = [
                {"bearerAuth": []}
            ]
    elif auth_mode == "apikey":
        base.setdefault("components", {}).setdefault("securitySchemes", {})[
            "apiKeyAuth"
        ] = {"type": "apiKey", "in": "header", "name": "Authorization"}
        base["paths"]["/search"]["post"]["security"] = [{"apiKeyAuth": []}]
    return base


# Custom Actions for ChatGPT (newer approach)
@app.get("/actions/schema")
async def actions_schema(request: Request, mode: Optional[str] = None):
    _mark_request("/actions/schema")
    """Schema for ChatGPT Custom Actions with selectable auth mode.

    Use query string: /actions/schema?mode=bearer or mode=none
    (default from env ACTIONS_AUTH_MODE).
    """
    effective_mode = (mode or os.getenv("ACTIONS_AUTH_MODE", "none")).strip().lower()
    if effective_mode not in ("none", "bearer"):
        effective_mode = "none"
    base_url = f"{request.url.scheme}://{request.headers.get('host')}"
    return _build_actions_schema(
        "bearer" if effective_mode == "bearer" else "none",
        base_url,
    )


@app.get("/metrics")
async def metrics_text():
    """Prometheus-like exposition and JSON metrics (simple)."""
    _mark_request("/metrics")
    # Prefer native Prometheus client when available
    if _PROM_AVAILABLE:
        output = generate_latest(_prom_registry)
        return Response(content=output, media_type=CONTENT_TYPE_LATEST)
    try:

        def _quantiles(values: List[float]):
            if not values:
                return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0}
            arr = sorted(values)
            n = len(arr)

            def q(p: float) -> float:
                idx = int(max(0, min(n - 1, round(p * (n - 1)))))
                return arr[idx]

            return {
                "p50": q(0.50),
                "p95": q(0.95),
                "p99": q(0.99),
                "avg": sum(arr) / n,
            }

        lines = []
        for route, val in sorted(_metrics["requests_total"].items()):
            lines.append(f'ragpp_requests_total{{route="{route}"}} {int(val)}')
        for route, val in sorted(_metrics["errors_total"].items()):
            lines.append(f'ragpp_errors_total{{route="{route}"}} {int(val)}')
        # Latency quantiles (ms)
        for route, samples in sorted(_latency_samples.items()):
            qs = _quantiles(list(samples))
            lines.append(f'ragpp_latency_ms_p50{{route="{route}"}} {qs["p50"]:.2f}')
            lines.append(f'ragpp_latency_ms_p95{{route="{route}"}} {qs["p95"]:.2f}')
            lines.append(f'ragpp_latency_ms_p99{{route="{route}"}} {qs["p99"]:.2f}')
            lines.append(f'ragpp_latency_ms_avg{{route="{route}"}} {qs["avg"]:.2f}')
        text_body = "\n".join(lines) + "\n"
        return Response(content=text_body, media_type="text/plain")
    except Exception:
        # Fallback JSON
        extra = {
            r: {
                "count": len(s),
                "last_ms": (list(s)[-1] if len(s) else 0.0),
            }
            for r, s in _latency_samples.items()
        }
        return JSONResponse({"metrics": _metrics, "latency": extra})


@app.get("/actions/schema/noauth")
async def actions_schema_noauth(request: Request):
    base_url = f"{request.url.scheme}://{request.headers.get('host')}"
    return _build_actions_schema("none", base_url)


@app.get("/actions/schema/bearer")
async def actions_schema_bearer(request: Request):
    base_url = f"{request.url.scheme}://{request.headers.get('host')}"
    return _build_actions_schema("bearer", base_url)


@app.get("/actions/schema/apikey")
async def actions_schema_apikey(request: Request):
    base_url = f"{request.url.scheme}://{request.headers.get('host')}"
    return _build_actions_schema("apikey", base_url)


# Memory API Models
class StoreMemoryRequest(BaseModel):
    content: str
    memory_type: str = "general"
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    importance_score: float = 0.5


class StoreConversationRequest(BaseModel):
    conversation_data: Dict[str, Any]
    title: Optional[str] = None
    importance_score: float = 0.5


class StoreProjectContextRequest(BaseModel):
    project_name: str = "pcs-meta-repo"
    context_type: str
    content: str
    metadata: Dict[str, Any] = {}


class SearchMemoryRequest(BaseModel):
    query: str
    memory_types: Optional[List[str]] = None
    max_results: int = 10
    importance_threshold: float = 0.3


class SystemAnalysisData(BaseModel):
    """Modelo para dados de análise do sistema dos últimos 7 dias."""

    report_metadata: Dict[str, Any]
    data_files: List[str]
    executive_summary: Dict[str, Any]
    git_changes: Optional[Dict[str, Any]] = None
    system_logs: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    error_analysis: Optional[Dict[str, Any]] = None
    config_changes: Optional[Dict[str, Any]] = None


class FeedAnalysisRequest(BaseModel):
    """Requisição para alimentar o servidor com dados de análise."""

    analysis_data: SystemAnalysisData
    processing_options: Dict[str, Any] = {}


class PaperData(BaseModel):
    """Modelo para dados de paper científico."""

    title: str
    authors: List[str]
    abstract: str
    url: str
    source: str  # arXiv, PubMed, SemanticScholar
    categories: List[str]
    published_date: str
    keywords: List[str]
    citation_count: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    significance_score: float = 0.0
    technical_concepts: List[str] = []
    methodology: str = ""
    results_summary: str = ""
    code_availability: bool = False


class FeedLiteratureRequest(BaseModel):
    """Requisição para alimentar o RAG++ com literatura científica."""

    papers: Dict[str, List[PaperData]]  # {area: [papers]}
    collection_metadata: Dict[str, Any] = {}
    processing_options: Dict[str, Any] = {}


class LiteratureStatsResponse(BaseModel):
    """Resposta com estatísticas da literatura no RAG++."""

    total_papers: int
    papers_by_area: Dict[str, int]
    papers_by_source: Dict[str, int]
    recent_papers: int  # últimos 30 dias
    high_impact_papers: int  # score > 3.0


# Tree Search Models
class TreeSearchRequest(BaseModel):
    """Requisição para busca em árvore."""

    query: str
    strategy: Optional[str] = "best_first"  # best_first, depth_first, breadth_first
    max_results: Optional[int] = 10
    node_types: Optional[List[str]] = None  # root, category, document, etc.
    min_score: Optional[float] = 0.0


class TreeNodeRequest(BaseModel):
    """Requisição para adicionar nó à árvore."""

    name: str
    content: str
    node_type: str = "document"  # root, category, document, section, etc.
    parent_id: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    score: Optional[float] = 0.0


class TreeStructureResponse(BaseModel):
    """Resposta com estrutura da árvore."""

    tree_id: str
    root_id: Optional[str]
    total_nodes: int
    max_depth: int
    structure: Dict[str, Any]


class TreeSearchResponse(BaseModel):
    """Resposta da busca em árvore."""

    query: str
    strategy: str
    results: List[Dict[str, Any]]
    total_found: int
    timestamp: str


# Memory service dependency
def get_memory():
    return get_memory_service()


# Memory API Endpoints
@app.post("/memory/store")
async def store_memory(request: StoreMemoryRequest, memory_service=Depends(get_memory)):
    """Armazena uma nova memória."""
    try:
        memory_id = memory_service.store_memory(
            content=request.content,
            memory_type=request.memory_type,
            tags=request.tags,
            metadata=request.metadata,
            importance_score=request.importance_score,
        )
        return {"memory_id": memory_id, "status": "stored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/store/conversation")
async def store_conversation_endpoint(
    request: StoreConversationRequest, memory_service=Depends(get_memory)
):
    """Armazena uma conversa completa."""
    try:
        conv_id = memory_service.store_conversation(
            conversation_data=request.conversation_data,
            title=request.title,
            importance_score=request.importance_score,
        )
        return {"conversation_id": conv_id, "status": "stored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/store/project")
async def store_project_context_endpoint(
    request: StoreProjectContextRequest, memory_service=Depends(get_memory)
):
    """Armazena contexto do projeto."""
    try:
        context_id = memory_service.store_project_context(
            project_name=request.project_name,
            context_type=request.context_type,
            content=request.content,
            metadata=request.metadata,
        )
        return {"context_id": context_id, "status": "stored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/search")
async def search_memory_endpoint(
    request: SearchMemoryRequest, memory_service=Depends(get_memory)
):
    """Busca na memória usando busca semântica."""
    try:
        results = memory_service.search_memory(
            query=request.query,
            memory_types=request.memory_types,
            max_results=request.max_results,
            importance_threshold=request.importance_threshold,
        )
        return {"query": request.query, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/recent")
async def get_recent_memories_endpoint(
    days: int = 7,
    memory_types: Optional[str] = None,
    max_results: int = 20,
    memory_service=Depends(get_memory),
):
    """Recupera memórias recentes."""
    try:
        types_list = memory_types.split(",") if memory_types else None
        results = memory_service.get_recent_memories(
            days=days, memory_types=types_list, max_results=max_results
        )
        return {"recent_memories": results, "count": len(results), "days": days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/project/status")
async def get_project_status_endpoint(
    project_name: str = "pcs-meta-repo", memory_service=Depends(get_memory)
):
    """Recupera status do projeto."""
    try:
        status = memory_service.get_project_status(project_name)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/stats")
async def get_memory_stats_endpoint(memory_service=Depends(get_memory)):
    """Estatísticas do serviço de memória."""
    try:
        stats = memory_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/chatgpt/context")
async def store_chatgpt_context(
    conversation_title: str,
    messages: List[Dict[str, str]],
    context_summary: str = "",
    importance_score: float = 0.7,
    memory_service=Depends(get_memory),
):
    """Armazena contexto de conversa do ChatGPT."""
    try:
        # Store as conversation
        conversation_data = {
            "messages": messages,
            "summary": context_summary,
            "source": "chatgpt",
            "timestamp": datetime.now().isoformat(),
        }

        conv_id = memory_service.store_conversation(
            conversation_data=conversation_data,
            title=conversation_title,
            importance_score=importance_score,
        )

        # Also store key insights as individual memories
        for i, msg in enumerate(messages):
            if msg.get("role") == "assistant" and len(msg.get("content", "")) > 100:
                memory_service.store_memory(
                    content=msg["content"],
                    memory_type="chatgpt_insight",
                    tags=["chatgpt", "insight", conversation_title],
                    metadata={
                        "conversation_id": conv_id,
                        "message_index": i,
                        "source": "chatgpt",
                    },
                    importance_score=importance_score * 0.8,
                )

        return {
            "conversation_id": conv_id,
            "status": "stored",
            "message_count": len(messages),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/chatgpt/recall")
async def recall_context(
    query: str,
    include_conversations: bool = True,
    include_insights: bool = True,
    max_results: int = 10,
    memory_service=Depends(get_memory),
):
    """Recupera contexto relevante para o ChatGPT."""
    try:
        memory_types = []
        if include_conversations:
            memory_types.extend(["conversation"])
        if include_insights:
            memory_types.extend(["chatgpt_insight", "insight", "context"])

        results = memory_service.search_memory(
            query=query,
            memory_types=memory_types if memory_types else None,
            max_results=max_results,
            importance_threshold=0.4,
        )

        # Format for ChatGPT consumption
        context_summary = []
        for result in results:
            content_preview = (
                result["content"][:500] + "..."
                if len(result["content"]) > 500
                else result["content"]
            )
            context_summary.append(
                {
                    "content": content_preview,
                    "type": result["memory_type"],
                    "relevance": result["relevance_score"],
                    "timestamp": result["timestamp"],
                    "tags": result["tags"],
                }
            )

        return {
            "query": query,
            "context": context_summary,
            "total_results": len(results),
            "summary": f"Found {len(results)} relevant memories for your query.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoint for feeding system analysis data
@app.post("/admin/feed-analysis-data")
async def feed_system_analysis_data(
    request_data: Dict[str, Any], memory_service=Depends(get_memory)
):
    """
    Endpoint para alimentar o servidor com dados de análise dos últimos 7 dias.
    Recebe dados de git, logs, métricas, erros e configurações.
    """
    try:
        # Extrair dados do relatório consolidado
        metadata = request_data.get("report_metadata", {})
        summary = request_data.get("executive_summary", {})

        # Gerar timestamp e identificadores
        timestamp = datetime.now().isoformat()
        analysis_period = metadata.get("period_days", 7)
        generated_at = metadata.get("generated_at", timestamp)

        # Extrair dados para melhor legibilidade
        services_status = summary.get("services_status", {})
        services_count = services_status.get("all_services_running", 0)
        connectivity = summary.get("connectivity_health", {})
        external_api_ok = connectivity.get("external_api_accessible", False)
        internal_api_ok = connectivity.get("internal_api_accessible", False)
        total_commits = summary.get("total_commits_period", 0)
        nginx_errors = summary.get("nginx_errors_period", 0)

        # 1. Armazenar resumo executivo
        executive_summary_content = f"""
        === ANÁLISE DO SISTEMA DOS ÚLTIMOS {analysis_period} DIAS ===
        
        Período: {analysis_period} dias (gerado em {generated_at})
        Hostname: {metadata.get("hostname", "unknown")}
        Sistema: {metadata.get("system_info", {}).get("os", "unknown")}
        Kernel: {metadata.get("system_info", {}).get("kernel", "unknown")}
        Uptime: {metadata.get("system_info", {}).get("uptime", "unknown")}
        
        RESUMO EXECUTIVO:
        - Total de commits no período: {total_commits}
        - Erros nginx no período: {nginx_errors}
        - Serviços rodando: {services_count}/3
        - API externa acessível: {external_api_ok}
        - API interna acessível: {internal_api_ok}
        
        Arquivos de dados gerados: {", ".join(request_data.get("data_files", []))}
        """

        memory_service.store_memory(
            content=executive_summary_content,
            memory_type="system_analysis",
            tags=["system", "7days", "analysis", "executive_summary"],
            metadata={
                "analysis_period_days": analysis_period,
                "generated_at": generated_at,
                "hostname": metadata.get("hostname"),
                "data_files_count": len(request_data.get("data_files", [])),
                "source": "automated_7days_collection",
            },
            importance_score=0.8,
        )

        # 2. Processar e armazenar dados detalhados se disponíveis
        stored_memories = 1  # Executive summary já armazenado

        # Dados de conectividade e saúde do sistema
        if "connectivity_health" in summary:
            connectivity_data = summary["connectivity_health"]
            external_status = (
                "✅ Acessível"
                if connectivity_data.get("external_api_accessible")
                else "❌ Inacessível"
            )
            internal_status = (
                "✅ Acessível"
                if connectivity_data.get("internal_api_accessible")
                else "❌ Inacessível"
            )

            nginx_status = "Running" if services_count > 0 else "Issues detected"
            cloudflared_status = "Running" if services_count > 1 else "Issues detected"
            ragpp_status = "Running" if services_count > 2 else "Issues detected"

            connectivity_content = f"""
            === ANÁLISE DE CONECTIVIDADE E SAÚDE ===
            
            API Externa (mcp.agourakis.med.br): {external_status}
            API Interna (127.0.0.1:8000): {internal_status}
            
            Status dos Serviços Críticos:
            - Nginx: {nginx_status}
            - Cloudflared: {cloudflared_status}
            - RAG++ MCP Server: {ragpp_status}
            
            Período de análise: {analysis_period} dias
            """

            memory_service.store_memory(
                content=connectivity_content,
                memory_type="system_health",
                tags=["connectivity", "health", "services", "7days"],
                metadata={
                    "external_api_status": (
                        connectivity_data.get("external_api_accessible")
                    ),
                    "internal_api_status": (
                        connectivity_data.get("internal_api_accessible")
                    ),
                    "services_running": services_count,
                    "analysis_date": generated_at,
                },
                importance_score=0.7,
            )
            stored_memories += 1

        # Dados de desenvolvimento (commits)
        if total_commits > 0:
            # Determinar nível de atividade
            if total_commits > 20:
                activity_msg = (
                    "⚠️ Atenção: Muitos commits podem indicar "
                    "desenvolvimento ativo ou correções urgentes."
                )
            elif 5 <= total_commits <= 20:
                activity_msg = "✅ Atividade normal de desenvolvimento."
            elif 1 <= total_commits < 5:
                activity_msg = "ℹ️ Baixa atividade de desenvolvimento no período."
            else:
                activity_msg = ""

            activity_level = (
                "alta"
                if total_commits > 10
                else "baixa"
                if total_commits > 0
                else "nenhuma"
            )

            dev_activity_content = f"""
            === ATIVIDADE DE DESENVOLVIMENTO ===
            
            Período: {analysis_period} dias
            Total de commits: {total_commits}
            
            Esta análise mostra {activity_level} atividade de desenvolvimento 
            no período analisado.
            
            {activity_msg}
            """

            memory_service.store_memory(
                content=dev_activity_content,
                memory_type="development_activity",
                tags=["git", "commits", "development", "7days"],
                metadata={
                    "total_commits": total_commits,
                    "period_days": analysis_period,
                    "analysis_date": generated_at,
                    "activity_level": "high" if total_commits > 10 else "low",
                },
                importance_score=0.6,
            )
            stored_memories += 1

        # Dados de erros nginx
        if nginx_errors > 0:
            # Determinar mensagens baseadas no número de erros
            if nginx_errors > 50:
                error_msg = (
                    "🚨 ALERTA: Alto número de erros nginx detectados! "
                    "Investigação necessária."
                )
            elif 10 <= nginx_errors <= 50:
                error_msg = "⚠️ Aviso: Alguns erros nginx detectados. Monitorar."
            elif 1 <= nginx_errors < 10:
                error_msg = "ℹ️ Poucos erros nginx - normal para o período."
            else:
                error_msg = ""

            error_analysis_content = f"""
            === ANÁLISE DE ERROS NGINX ===
            
            Período: {analysis_period} dias
            Total de erros nginx: {nginx_errors}
            
            {error_msg}
            
            Recomendações:
            - Verificar logs detalhados: /var/log/nginx/error.log
            - Analisar padrões de erro
            - Verificar configuração nginx
            """

            # Determinar severidade
            if nginx_errors > 50:
                severity = "high"
                importance = 0.9
            elif nginx_errors > 10:
                severity = "medium"
                importance = 0.7
            else:
                severity = "low"
                importance = 0.7

            memory_service.store_memory(
                content=error_analysis_content,
                memory_type="error_analysis",
                tags=["nginx", "errors", "monitoring", "7days"],
                metadata={
                    "error_count": nginx_errors,
                    "severity": severity,
                    "period_days": analysis_period,
                    "analysis_date": generated_at,
                },
                importance_score=importance,
            )
            stored_memories += 1

        # Armazenar dados brutos para referência futura
        raw_data_content = f"""
        === DADOS BRUTOS DA ANÁLISE ===
        
        Dados completos da análise dos últimos {analysis_period} dias 
        salvos para referência.
        
        Estrutura dos dados:
        - Metadados do relatório
        - Resumo executivo
        - Arquivos de dados: {len(request_data.get("data_files", []))} arquivos
        
        Para acessar dados detalhados, consulte os arquivos específicos 
        ou solicite análise mais profunda.
        
        Timestamp da coleta: {generated_at}
        """

        memory_service.store_memory(
            content=raw_data_content,
            memory_type="raw_analysis_data",
            tags=["raw_data", "7days", "reference", "backup"],
            metadata={
                "raw_data": request_data,  # Dados completos
                "analysis_date": generated_at,
                "data_size": len(str(request_data)),
                "source": "automated_collection",
            },
            importance_score=0.5,
        )
        stored_memories += 1

        return {
            "status": "success",
            "message": (
                f"Dados de análise dos últimos {analysis_period} dias "
                "processados e armazenados"
            ),
            "memories_stored": stored_memories,
            "analysis_period_days": analysis_period,
            "generated_at": generated_at,
            "summary": {
                "commits": total_commits,
                "nginx_errors": nginx_errors,
                "services_healthy": services_count == 3,
                "external_api_accessible": external_api_ok,
                "internal_api_accessible": internal_api_ok,
            },
        }

    except Exception as e:
        logger.error(f"Erro ao processar dados de análise: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar dados de análise: {str(e)}"
        )


@app.post("/admin/feed-literature")
async def feed_literature_data(
    request: FeedLiteratureRequest, memory_service=Depends(get_memory)
):
    """
    Endpoint para alimentar o RAG++ com literatura científica recente.
    Processa e armazena papers categorizados por área de pesquisa.
    """
    try:
        timestamp = datetime.now().isoformat()
        stored_memories = 0
        processed_papers = 0

        # Estatísticas da coleta
        total_papers = sum(len(papers) for papers in request.papers.values())
        high_impact_papers = 0
        papers_by_source = {}

        # Processar papers por área
        for area, papers in request.papers.items():
            area_papers = []
            for paper in papers:
                processed_papers += 1

                # Contar papers por fonte
                papers_by_source[paper.source] = (
                    papers_by_source.get(paper.source, 0) + 1
                )

                # Contar papers de alto impacto
                if paper.significance_score > 3.0:
                    high_impact_papers += 1

                # Preparar conteúdo estruturado
                paper_content = f"""
=== {paper.title} ===

AUTORES: {', '.join(paper.authors)}
FONTE: {paper.source} | PUBLICADO: {paper.published_date}
URL: {paper.url}
DOI: {paper.doi or 'N/A'} | VENUE: {paper.venue or 'N/A'}
CITAÇÕES: {paper.citation_count or 0}
SCORE DE SIGNIFICÂNCIA: {paper.significance_score}/5.0

ABSTRACT:
{paper.abstract}

CATEGORIAS: {', '.join(paper.categories)}
PALAVRAS-CHAVE: {', '.join(paper.keywords)}
CONCEITOS TÉCNICOS: {', '.join(paper.technical_concepts)}

METODOLOGIA:
{paper.methodology or 'Não especificada'}

RESUMO DOS RESULTADOS:
{paper.results_summary or 'Não disponível'}

CÓDIGO DISPONÍVEL: {'Sim' if paper.code_availability else 'Não'}
                """

                area_papers.append(
                    {
                        "title": paper.title,
                        "authors": paper.authors,
                        "significance_score": paper.significance_score,
                        "source": paper.source,
                        "url": paper.url,
                    }
                )

            # Armazenar compilação da área
            if area_papers:
                area_summary = f"""
=== LITERATURA RECENTE: {area.upper()} ===

Coletados {len(area_papers)} papers relevantes em {area}
Data da coleta: {timestamp}

PAPERS POR SIGNIFICÂNCIA:
"""
                # Ordenar por significância
                area_papers_sorted = sorted(
                    area_papers, key=lambda x: x["significance_score"], reverse=True
                )

                for i, paper in enumerate(area_papers_sorted[:10], 1):  # Top 10
                    area_summary += f"""
{i}. {paper['title']} (Score: {paper['significance_score']})
   Autores: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}
   Fonte: {paper['source']} | URL: {paper['url']}
"""

                # Estatísticas da área
                avg_significance = sum(
                    p["significance_score"] for p in area_papers
                ) / len(area_papers)
                area_summary += f"""

ESTATÍSTICAS DA ÁREA:
- Total de papers: {len(area_papers)}
- Significância média: {avg_significance:.2f}
- Papers de alto impacto (>3.0): {sum(1 for p in area_papers if p['significance_score'] > 3.0)}
- Fontes: {', '.join(set(p['source'] for p in area_papers))}
"""

                memory_service.store_memory(
                    content=area_summary,
                    memory_type="literature_summary",
                    tags=["literature", "research", area, "summary", "recent"],
                    metadata={
                        "area": area,
                        "paper_count": len(area_papers),
                        "avg_significance": avg_significance,
                        "collection_date": timestamp,
                        "high_impact_count": sum(
                            1 for p in area_papers if p["significance_score"] > 3.0
                        ),
                    },
                    importance_score=min(0.9, avg_significance / 5.0 + 0.3),
                )
                stored_memories += 1

            # Armazenar papers individuais de alto impacto
            for paper in papers:
                if (
                    paper.significance_score >= 3.5
                ):  # Apenas papers de muito alto impacto
                    memory_service.store_memory(
                        content=paper_content,
                        memory_type="research_paper",
                        tags=["paper", "research", area, paper.source, "high-impact"]
                        + paper.technical_concepts[:5],
                        metadata={
                            "title": paper.title,
                            "authors": paper.authors,
                            "significance_score": paper.significance_score,
                            "area": area,
                            "source": paper.source,
                            "url": paper.url,
                            "published_date": paper.published_date,
                            "citation_count": paper.citation_count,
                            "technical_concepts": paper.technical_concepts,
                        },
                        importance_score=min(
                            0.95, paper.significance_score / 5.0 + 0.2
                        ),
                    )
                    stored_memories += 1

        # Armazenar estatísticas globais da coleta
        global_summary = f"""
=== COLETA DE LITERATURA CIENTÍFICA ===

Data: {timestamp}
Total de papers processados: {total_papers}
Papers de alto impacto (>3.0): {high_impact_papers}

DISTRIBUIÇÃO POR ÁREA:
{chr(10).join(f"- {area}: {len(papers)} papers" for area, papers in request.papers.items())}

DISTRIBUIÇÃO POR FONTE:
{chr(10).join(f"- {source}: {count} papers" for source, count in papers_by_source.items())}

METADADOS DA COLETA:
{request.collection_metadata}

Esta coleta enriquece a base de conhecimento com os avanços mais recentes
em modelagem, estatística, gráficos e matemática aplicados ao projeto.
        """

        memory_service.store_memory(
            content=global_summary,
            memory_type="literature_collection",
            tags=["literature", "collection", "statistics", "metadata"],
            metadata={
                "total_papers": total_papers,
                "high_impact_papers": high_impact_papers,
                "areas": list(request.papers.keys()),
                "sources": list(papers_by_source.keys()),
                "collection_date": timestamp,
                "papers_by_source": papers_by_source,
            },
            importance_score=0.8,
        )
        stored_memories += 1

        return {
            "status": "success",
            "message": "Literatura científica processada e integrada ao RAG++",
            "memories_stored": stored_memories,
            "papers_processed": processed_papers,
            "collection_stats": {
                "total_papers": total_papers,
                "high_impact_papers": high_impact_papers,
                "areas_covered": len(request.papers),
                "papers_by_source": papers_by_source,
                "avg_significance": sum(
                    sum(p.significance_score for p in papers) / len(papers)
                    for papers in request.papers.values()
                )
                / len(request.papers)
                if request.papers
                else 0,
            },
        }

    except Exception as e:
        logger.error(f"Erro ao processar literatura científica: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar literatura científica: {str(e)}"
        )


@app.get("/admin/literature-stats", response_model=LiteratureStatsResponse)
async def get_literature_stats(memory_service=Depends(get_memory)):
    """Retorna estatísticas da literatura armazenada no RAG++."""
    try:
        # Buscar papers armazenados
        paper_memories = memory_service.search_memory(
            query="research paper literature",
            memory_types=[
                "research_paper",
                "literature_summary",
                "literature_collection",
            ],
            max_results=1000,
        )

        # Calcular estatísticas
        total_papers = len(
            [m for m in paper_memories if m["memory_type"] == "research_paper"]
        )

        # Papers por área (extrair dos tags)
        papers_by_area = {}
        papers_by_source = {}
        high_impact_papers = 0
        recent_papers = 0

        thirty_days_ago = datetime.now() - timedelta(days=30)

        for memory in paper_memories:
            if memory["memory_type"] == "research_paper":
                metadata = memory.get("metadata", {})

                # Área (primeiro tag que não seja padrão)
                area_tag = next(
                    (
                        tag
                        for tag in memory.get("tags", [])
                        if tag not in ["paper", "research", "high-impact"]
                    ),
                    "unknown",
                )
                papers_by_area[area_tag] = papers_by_area.get(area_tag, 0) + 1

                # Fonte
                source = metadata.get("source", "unknown")
                papers_by_source[source] = papers_by_source.get(source, 0) + 1

                # Alto impacto
                significance = metadata.get("significance_score", 0)
                if significance > 3.0:
                    high_impact_papers += 1

                # Recentes
                timestamp_str = memory.get("timestamp", "")
                try:
                    memory_date = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )
                    if memory_date.replace(tzinfo=None) > thirty_days_ago:
                        recent_papers += 1
                except Exception:
                    pass

        return LiteratureStatsResponse(
            total_papers=total_papers,
            papers_by_area=papers_by_area,
            papers_by_source=papers_by_source,
            recent_papers=recent_papers,
            high_impact_papers=high_impact_papers,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Tree Search Endpoints
@app.post("/tree/search", response_model=TreeSearchResponse)
async def tree_search(request: TreeSearchRequest):
    """Buscar na árvore hierárquica usando diferentes estratégias."""
    if not tree_search_engine:
        raise HTTPException(
            status_code=503, detail="Tree search engine not initialized"
        )

    try:
        from ragpp.tree_search_optimized import NodeType, SearchStrategy

        # Convert strategy string to enum
        strategy_map = {
            "best_first": SearchStrategy.BEST_FIRST,
            "depth_first": SearchStrategy.DEPTH_FIRST,
            "breadth_first": SearchStrategy.BREADTH_FIRST,
            "a_star": SearchStrategy.A_STAR,
            "iterative_deepening": SearchStrategy.ITERATIVE_DEEPENING,
        }

        strategy = strategy_map.get(request.strategy, SearchStrategy.BEST_FIRST)

        # Convert node types if provided
        node_types = None
        if request.node_types:
            node_type_map = {
                "root": NodeType.ROOT,
                "category": NodeType.CATEGORY,
                "document": NodeType.DOCUMENT,
                "section": NodeType.SECTION,
                "concept": NodeType.CONCEPT,
                "reference": NodeType.REFERENCE,
                "memory": NodeType.MEMORY,
                "search_result": NodeType.SEARCH_RESULT,
            }
            node_types = [
                node_type_map.get(nt)
                for nt in request.node_types
                if nt in node_type_map
            ]

        # Perform search
        results = tree_search_engine.search(
            query=request.query,
            strategy=strategy,
            max_results=request.max_results or 10,
            node_types=node_types,
            min_score=request.min_score or 0.0,
        )

        # Convert results to response format
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "node_id": result.node.id,
                    "name": result.node.name,
                    "content": result.node.content,
                    "node_type": result.node.node_type.value,
                    "relevance_score": result.relevance_score,
                    "path": result.path,
                    "tags": result.node.tags,
                    "metadata": result.node.metadata,
                    "score": result.node.score,
                    "depth": result.node.depth,
                }
            )

        return TreeSearchResponse(
            query=request.query,
            strategy=request.strategy,
            results=formatted_results,
            total_found=len(results),
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Tree search error: {e}")
        raise HTTPException(status_code=500, detail=f"Tree search failed: {str(e)}")


@app.post("/tree/add_node")
async def add_tree_node(request: TreeNodeRequest):
    """Adicionar novo nó à árvore."""
    if not tree_search_engine:
        raise HTTPException(
            status_code=503, detail="Tree search engine not initialized"
        )

    try:
        from ragpp.tree_search_optimized import NodeType, TreeNode

        # Convert node type string to enum
        node_type_map = {
            "root": NodeType.ROOT,
            "category": NodeType.CATEGORY,
            "document": NodeType.DOCUMENT,
            "section": NodeType.SECTION,
            "concept": NodeType.CONCEPT,
            "reference": NodeType.REFERENCE,
            "memory": NodeType.MEMORY,
            "search_result": NodeType.SEARCH_RESULT,
        }

        node_type = node_type_map.get(request.node_type, NodeType.DOCUMENT)

        # Create new node
        node = TreeNode(
            name=request.name,
            content=request.content,
            node_type=node_type,
            tags=request.tags or [],
            metadata=request.metadata or {},
            score=request.score or 0.0,
        )

        # Add to tree
        node_id = tree_search_engine.add_node(node, request.parent_id)

        return {
            "node_id": node_id,
            "status": "added",
            "message": f"Node '{request.name}' added successfully",
        }

    except Exception as e:
        logger.error(f"Add node error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add node: {str(e)}")


@app.get("/tree/structure", response_model=TreeStructureResponse)
async def get_tree_structure(node_id: Optional[str] = None, max_depth: int = 3):
    """Obter estrutura da árvore para visualização."""
    if not tree_search_engine:
        raise HTTPException(
            status_code=503, detail="Tree search engine not initialized"
        )

    try:
        structure = tree_search_engine.get_tree_structure(node_id, max_depth)

        return TreeStructureResponse(
            tree_id="main",
            root_id=tree_search_engine.root_id,
            total_nodes=len(tree_search_engine.nodes),
            max_depth=max(
                (node.depth for node in tree_search_engine.nodes.values()), default=0
            ),
            structure=structure,
        )

    except Exception as e:
        logger.error(f"Tree structure error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get tree structure: {str(e)}"
        )


@app.get("/tree/export")
async def export_tree():
    """Exportar árvore completa para JSON."""
    if not tree_search_engine:
        raise HTTPException(
            status_code=503, detail="Tree search engine not initialized"
        )

    try:
        return tree_search_engine.export_tree()

    except Exception as e:
        logger.error(f"Tree export error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export tree: {str(e)}")


@app.post("/tree/populate_from_memories")
async def populate_tree_from_memories():
    """Popular árvore com memórias existentes do RAG++."""
    if not tree_search_engine:
        raise HTTPException(
            status_code=503, detail="Tree search engine not initialized"
        )

    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        from ragpp.tree_search_optimized import NodeType, TreeNode

        # Get memory service
        memory_service = get_memory_service()

        # Search for memories
        memories = memory_service.search_memories(
            query="",
            memory_types=["research_paper", "literature_summary", "conversation"],
            max_results=100,
        )

        added_count = 0

        # Get categories
        categories = {}
        for category_node in tree_search_engine.get_children(
            tree_search_engine.root_id
        ):
            categories[category_node.name.lower()] = category_node.id

        # Add memories as nodes
        for memory in memories:
            # Determine category based on tags or content
            category_id = None
            for tag in memory.get("tags", []):
                if tag.lower() in categories:
                    category_id = categories[tag.lower()]
                    break

            if not category_id:
                # Default to Machine Learning category
                category_id = (
                    list(categories.values())[0]
                    if categories
                    else tree_search_engine.root_id
                )

            # Create node from memory
            node = TreeNode(
                name=memory.get("content", "")[:100] + "..."
                if len(memory.get("content", "")) > 100
                else memory.get("content", ""),
                content=memory.get("content", ""),
                node_type=NodeType.MEMORY,
                tags=memory.get("tags", []),
                metadata={
                    "memory_id": memory.get("id"),
                    "memory_type": memory.get("memory_type"),
                    "timestamp": memory.get("timestamp"),
                },
                score=memory.get("importance", 0.0),
            )

            # Add to tree
            tree_search_engine.add_node(node, category_id)
            added_count += 1

        return {
            "status": "success",
            "added_nodes": added_count,
            "message": f"Added {added_count} memories to tree structure",
        }

    except Exception as e:
        logger.error(f"Populate tree error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to populate tree: {str(e)}"
        )


# ============================================================================
# MULTI-AI CACHE ENDPOINTS - Sistema de Cache Inteligente entre IAs
# ============================================================================

# Importar endpoints do cache multi-IA
try:
    # Import models and functions from multi_ai_cache_endpoints
    sys.path.append(str(Path(__file__).parent.parent))
    from multi_ai_cache_endpoints import (
        AIContextStore,
        AISessionRequest,
        CrossAITransfer,
        SmartCacheQuery,
        create_ai_session_endpoint,
        cross_ai_transfer_endpoint,
        get_ai_cache_stats_endpoint,
        retrieve_ai_context_endpoint,
        smart_cache_search_endpoint,
        store_ai_context_endpoint,
    )

    # Registrar endpoints de cache multi-IA
    @app.post("/ai/sessions")
    async def create_ai_session(
        request: AISessionRequest, memory_service=Depends(get_memory)
    ):
        """Criar nova sessão de IA com cache inteligente."""
        return create_ai_session_endpoint(request, memory_service)

    @app.post("/ai/sessions/{session_id}/context")
    async def store_ai_context(
        session_id: str, request: AIContextStore, memory_service=Depends(get_memory)
    ):
        """Armazenar contexto de conversa de IA com cache inteligente."""
        return store_ai_context_endpoint(session_id, request, memory_service)

    @app.get("/ai/sessions/{session_id}/context")
    async def retrieve_ai_context(
        session_id: str,
        include_messages: bool = True,
        max_messages: int = 50,
        memory_service=Depends(get_memory),
    ):
        """Recuperar contexto de sessão de IA."""
        return retrieve_ai_context_endpoint(
            session_id, include_messages, max_messages, memory_service
        )

    @app.post("/ai/transfer")
    async def cross_ai_transfer(
        request: CrossAITransfer, memory_service=Depends(get_memory)
    ):
        """Transferir contexto entre diferentes IAs."""
        return cross_ai_transfer_endpoint(request, memory_service)

    @app.post("/ai/cache/search")
    async def smart_cache_search(
        request: SmartCacheQuery, memory_service=Depends(get_memory)
    ):
        """Busca inteligente no cache multi-IA."""
        return smart_cache_search_endpoint(request, memory_service)

    @app.get("/ai/cache/stats")
    async def get_ai_cache_stats(memory_service=Depends(get_memory)):
        """Estatísticas do sistema de cache multi-IA."""
        return get_ai_cache_stats_endpoint(memory_service)

    @app.get("/ai/sessions")
    async def list_ai_sessions(
        ai_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
        memory_service=Depends(get_memory),
    ):
        """Listar sessões de IA ativas e recentes."""
        try:
            # Buscar sessões no memory service
            query = "ai_session"
            if ai_type:
                query += f" AND ai_type:{ai_type}"
            if user_id:
                query += f" AND user_id:{user_id}"

            sessions = memory_service.search_memory(
                query=query, memory_types=["ai_session"], max_results=limit
            )

            # Importar cache ativo
            from multi_ai_cache_endpoints import _active_sessions

            # Formatar resultado
            active_sessions = []
            archived_sessions = []

            for session in sessions:
                metadata = session.get("metadata", {})
                session_data = metadata.get("session_data", {})
                session_id = session_data.get("session_id", "unknown")

                formatted_session = {
                    "session_id": session_id,
                    "ai_type": session_data.get("ai_type", "unknown"),
                    "session_name": session_data.get("session_name", "Unnamed"),
                    "user_id": session_data.get("user_id", "unknown"),
                    "created_at": session_data.get("created_at"),
                    "last_activity": session_data.get("last_activity"),
                    "message_count": session_data.get("message_count", 0),
                    "status": session_data.get("status", "unknown"),
                    "is_active": session_id in _active_sessions,
                }

                if session_id in _active_sessions:
                    active_sessions.append(formatted_session)
                else:
                    archived_sessions.append(formatted_session)

            return {
                "active_sessions": active_sessions,
                "archived_sessions": archived_sessions,
                "total_found": len(sessions),
                "cache_active_count": len(_active_sessions),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Erro ao listar sessões: {str(e)}"
            )

    @app.delete("/ai/sessions/{session_id}")
    async def delete_ai_session(session_id: str, memory_service=Depends(get_memory)):
        """Deletar sessão de IA e seu contexto."""
        try:
            from multi_ai_cache_endpoints import _active_sessions, _ai_conversations

            # Remover do cache ativo
            if session_id in _active_sessions:
                del _active_sessions[session_id]

            if session_id in _ai_conversations:
                del _ai_conversations[session_id]

            # Buscar e "arquivar" no memory service (não deletar realmente)
            session_memories = memory_service.search_memory(
                query=f"session_id:{session_id}",
                memory_types=["ai_session", "ai_context"],
                max_results=50,
            )

            archived_count = 0
            for memory in session_memories:
                # Marcar como arquivada
                metadata = memory.get("metadata", {})
                metadata["archived"] = True
                metadata["archived_at"] = datetime.now().isoformat()

                # Atualizar tags
                tags = memory.get("tags", [])
                if "archived" not in tags:
                    tags.append("archived")

                # Re-armazenar com status arquivado
                memory_service.store_memory(
                    content=memory.get("content", "")
                    + f"\n\n[ARQUIVADO EM {datetime.now().isoformat()}]",
                    memory_type=memory.get("memory_type", "unknown") + "_archived",
                    tags=tags,
                    metadata=metadata,
                    importance_score=memory.get("importance", 0)
                    * 0.5,  # Reduzir importância
                )
                archived_count += 1

            return {
                "status": "deleted",
                "session_id": session_id,
                "archived_memories": archived_count,
                "removed_from_cache": True,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Erro ao deletar sessão: {str(e)}"
            )

    logger.info("✅ Multi-AI Cache endpoints registered successfully")

except ImportError as e:
    logger.warning(f"⚠️ Multi-AI Cache endpoints not available: {e}")
except Exception as e:
    logger.error(f"❌ Error registering Multi-AI Cache endpoints: {e}")

# Register Import endpoints for conversation migration
try:
    from .import_endpoints import router as import_router

    app.include_router(import_router)
    logger.info("✅ Import endpoints registered successfully")

except ImportError as e:
    logger.warning(f"⚠️ Import endpoints not available: {e}")
except Exception as e:
    logger.error(f"❌ Error registering Import endpoints: {e}")


if __name__ == "__main__":
    # Configuration
    host = os.getenv("RAG_HOST", "0.0.0.0")
    port = int(os.getenv("RAG_PORT", "8000"))
    workers = int(os.getenv("RAG_WORKERS", "4"))  # Otimizado para 12 cores
    reload_flag = os.getenv("RAG_RELOAD", "0").strip().lower() in ("1", "true", "yes")

    print(f"🚀 Starting RAG++ Web Server on {host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔗 Plugin Manifest: http://{host}:{port}/.well-known/ai-plugin.json")
    print(f"🧠 Extended Memory API: http://{host}:{port}/memory/")
    print(f"⚡ Workers: {workers} (otimizado para {multiprocessing.cpu_count()} cores)")

    # Run server with optimized settings
    uvicorn.run(
        "ragpp_web_server:app",
        host=host,
        port=port,
        workers=workers,  # Múltiplos workers para melhor performance
        reload=reload_flag,
        log_level="info",
        # Otimizações de performance
        loop="uvloop" if os.getenv("USE_UVLOOP", "1") == "1" else "asyncio",
        http="httptools" if os.getenv("USE_HTTPTOOLS", "1") == "1" else "auto",
        # Configurações de timeout otimizadas
        access_log=False if os.getenv("PRODUCTION", "0") == "1" else True,
    )
