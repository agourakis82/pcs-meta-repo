#!/usr/bin/env python3
"""
RAG++ Official MCP Server Implementation
Following OpenAI's Model Context Protocol specifications.
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        EmbeddedResource,
        ImageContent,
        ListResourcesRequest,
        ListResourcesResult,
        ListToolsRequest,
        ListToolsResult,
        ReadResourceRequest,
        ReadResourceResult,
        Resource,
        TextContent,
        Tool,
    )
except ImportError:
    print("MCP package not found. Installing...")
    import subprocess

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "model-context-protocol"]
    )
    from mcp import ClientSession, StdioServerParameters
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        EmbeddedResource,
        ImageContent,
        ListResourcesRequest,
        ListResourcesResult,
        ListToolsRequest,
        ListToolsResult,
        ReadResourceRequest,
        ReadResourceResult,
        Resource,
        TextContent,
        Tool,
    )

# Import our RAG++ components
try:
    from ragpp.tools.mcp_rag_integration import MCPRAGIntegration
    from ragpp.tools.psychiatric_research_collector import PsychiatricResearchCollector
except ImportError as e:
    logging.warning(f"Could not import RAG++ components: {e}")
    MCPRAGIntegration = None
    PsychiatricResearchCollector = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    """Structure for RAG search results."""

    content: str
    source: str
    confidence: float
    metadata: Dict[str, Any]


class RAGPlusMCPServer:
    """RAG++ MCP Server following OpenAI specifications."""

    def __init__(self):
        self.server = Server("ragpp-mcp-server")
        self.rag_system: Optional[MCPRAGIntegration] = None
        self.research_collector: Optional[PsychiatricResearchCollector] = None
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP request handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return [
                # ChatGPT Connector required aliases
                Tool(
                    name="search",
                    description="Unified search across RAG index and project memory (ChatGPT MCP connector contract)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Free-text query",
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Maximum results to return",
                                "default": 8,
                            },
                            "target": {
                                "type": "string",
                                "enum": ["memory", "rag"],
                                "description": "Restrict search to a single backend (optional)",
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="fetch",
                    description="Fetch full document by id returned from search (ChatGPT MCP connector contract)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Opaque id from search results (prefixed with 'lit:' or 'mem:')",
                            }
                        },
                        "required": ["id"],
                    },
                ),
                Tool(
                    name="search_literature",
                    description="Search scientific literature using hybrid RAG++ system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Research question or keywords to search for",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 10,
                            },
                            "search_type": {
                                "type": "string",
                                "enum": ["hybrid", "literature", "memory"],
                                "description": "Type of search to perform",
                                "default": "hybrid",
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="store_research_finding",
                    description="Store a new research finding in the knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Title of the research finding",
                            },
                            "content": {
                                "type": "string",
                                "description": "Content or summary of the finding",
                            },
                            "source": {
                                "type": "string",
                                "description": "Source of the information",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata (authors, journal, year, etc.)",
                            },
                        },
                        "required": ["title", "content"],
                    },
                ),
                Tool(
                    name="get_recent_findings",
                    description="Retrieve recent research findings from the knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of findings to return",
                                "default": 20,
                            },
                            "category": {
                                "type": "string",
                                "description": "Filter by category (optional)",
                            },
                        },
                    },
                ),
                Tool(
                    name="collect_new_research",
                    description="Collect new research papers from PubMed on specified topics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topics": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Research topics to search for",
                            },
                            "years": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "Years to search (default: recent years)",
                            },
                            "max_papers": {
                                "type": "integer",
                                "description": "Maximum papers to collect per topic",
                                "default": 50,
                            },
                        },
                        "required": ["topics"],
                    },
                ),
                Tool(
                    name="synthesize_knowledge",
                    description="Synthesize knowledge across multiple research papers on a topic",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Topic to synthesize knowledge about",
                            },
                            "focus_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific areas to focus on (optional)",
                            },
                        },
                        "required": ["topic"],
                    },
                ),
                Tool(
                    name="store_chat_context",
                    description=(
                        "Store a ChatGPT/Gemini conversation context in the Extended Memory Service"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "conversation_title": {
                                "type": "string",
                                "description": "Title for this conversation/session",
                            },
                            "messages": {
                                "type": "array",
                                "description": "Conversation messages (role/content)",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "role": {"type": "string"},
                                        "content": {"type": "string"},
                                    },
                                    "required": ["role", "content"],
                                },
                            },
                            "context_summary": {
                                "type": "string",
                                "description": "Optional summary of the context",
                            },
                            "importance_score": {
                                "type": "number",
                                "description": "Importance score (0-1)",
                                "default": 0.7,
                            },
                        },
                        "required": ["conversation_title", "messages"],
                    },
                ),
                Tool(
                    name="recall_context",
                    description="Recall relevant project context from Extended Memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Recall query"},
                            "include_conversations": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include stored conversations",
                            },
                            "include_insights": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include assistant insights",
                            },
                            "max_results": {
                                "type": "integer",
                                "default": 10,
                                "description": "Max results",
                            },
                        },
                        "required": ["query"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "search":
                    return await self._alias_search(arguments)
                elif name == "fetch":
                    return await self._alias_fetch(arguments)
                if name == "search_literature":
                    return await self._search_literature(arguments)
                elif name == "store_research_finding":
                    return await self._store_research_finding(arguments)
                elif name == "get_recent_findings":
                    return await self._get_recent_findings(arguments)
                elif name == "collect_new_research":
                    return await self._collect_new_research(arguments)
                elif name == "synthesize_knowledge":
                    return await self._synthesize_knowledge(arguments)
                elif name == "store_chat_context":
                    return await self._store_chat_context(arguments)
                elif name == "recall_context":
                    return await self._recall_context(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text", text=f"Error executing {name}: {str(e)}"
                        )
                    ],
                    isError=True,
                )

        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available resources."""
            resources = [
                Resource(
                    uri="ragpp://database/status",
                    name="RAG++ Database Status",
                    description="Current status and statistics of the RAG++ knowledge base",
                    mimeType="application/json",
                ),
                Resource(
                    uri="ragpp://database/indexed_papers",
                    name="Indexed Research Papers",
                    description="List of all indexed research papers in the knowledge base",
                    mimeType="application/json",
                ),
                Resource(
                    uri="ragpp://config/system",
                    name="System Configuration",
                    description="Current RAG++ system configuration and capabilities",
                    mimeType="application/json",
                ),
            ]

            # Add dynamic resources for recent findings
            if self.rag_system:
                try:
                    recent = await self._get_recent_findings({"limit": 10})
                    if hasattr(recent, "content") and recent.content:
                        resources.append(
                            Resource(
                                uri="ragpp://findings/recent",
                                name="Recent Research Findings",
                                description="Latest research findings in the knowledge base",
                                mimeType="application/json",
                            )
                        )
                except Exception as e:
                    logger.warning(f"Could not add recent findings resource: {e}")

            return resources

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ReadResourceResult:
            """Read resource content."""
            try:
                if uri == "ragpp://database/status":
                    status = await self._get_database_status()
                    return ReadResourceResult(
                        contents=[
                            TextContent(type="text", text=json.dumps(status, indent=2))
                        ]
                    )
                elif uri == "ragpp://database/indexed_papers":
                    papers = await self._get_indexed_papers()
                    return ReadResourceResult(
                        contents=[
                            TextContent(type="text", text=json.dumps(papers, indent=2))
                        ]
                    )
                elif uri == "ragpp://config/system":
                    config = await self._get_system_config()
                    return ReadResourceResult(
                        contents=[
                            TextContent(type="text", text=json.dumps(config, indent=2))
                        ]
                    )
                elif uri == "ragpp://findings/recent":
                    findings = await self._get_recent_findings({"limit": 10})
                    return ReadResourceResult(
                        contents=[
                            TextContent(
                                type="text",
                                text=str(
                                    findings.content[0].text
                                    if findings.content
                                    else "No recent findings"
                                ),
                            )
                        ]
                    )
                else:
                    raise ValueError(f"Unknown resource: {uri}")

            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text", text=f"Error reading resource: {str(e)}"
                        )
                    ]
                )

    async def _initialize_rag_system(self):
        """Initialize the RAG++ system."""
        if not self.rag_system and MCPRAGIntegration:
            try:
                self.rag_system = MCPRAGIntegration()
                await asyncio.to_thread(self.rag_system.initialize)
                logger.info("RAG++ system initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize RAG++ system: {e}")

        if not self.research_collector and PsychiatricResearchCollector:
            try:
                self.research_collector = PsychiatricResearchCollector()
                logger.info("Research collector initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize research collector: {e}")

    # --- ChatGPT MCP alias implementations ---
    async def _alias_search(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Alias `search` → unified search with minimal contract for ChatGPT connector.

        Returns JSON: { "results": [{"id","score","title?","snippet?"}] }
        """
        query = arguments.get("query", "")
        top_k = int(arguments.get("top_k", 8) or 8)
        target = arguments.get("target")  # "memory" | "rag" | None

        await self._initialize_rag_system()

        results: List[Dict[str, Any]] = []

        # 1) RAG search
        if target in (None, "rag") and getattr(self.rag_system, "lit_collection", None):
            try:
                col = self.rag_system.lit_collection
                rag = await asyncio.to_thread(
                    col.query,
                    query_texts=[query],
                    n_results=min(max(1, top_k), 25),
                    include=["documents", "metadatas", "ids", "distances"],
                )
                ids = rag.get("ids", [[]])[0] if rag.get("ids") else []
                docs = rag.get("documents", [[]])[0] if rag.get("documents") else []
                metas = rag.get("metadatas", [[]])[0] if rag.get("metadatas") else []
                dists = rag.get("distances", [[]])[0] if rag.get("distances") else []

                for _id, doc, meta, dist in zip(ids, docs, metas, dists):
                    try:
                        score = 1.0 - float(dist) if dist is not None else 0.5
                    except Exception:
                        score = 0.5
                    # Clamp
                    score = max(0.0, min(1.0, score))
                    title = (
                        (meta or {}).get("title")
                        or (meta or {}).get("section")
                        or (meta or {}).get("record_id")
                        or str(_id)
                    )
                    snippet = (doc or "")[:200]
                    results.append(
                        {
                            "id": f"lit:{_id}",
                            "score": score,
                            "title": title,
                            "snippet": snippet,
                        }
                    )
            except Exception as e:
                logger.warning(f"RAG alias search failed: {e}")

        # 2) Memory search (no stdout printing)
        if target in (None, "memory"):
            try:
                # Lazy import to avoid optional dependency at server import-time
                from scripts.memory_manager import PCSMemoryManager  # type: ignore

                mgr = PCSMemoryManager()
                q = (query or "").lower()

                mems: List[Dict[str, Any]] = []
                for mem in getattr(mgr, "memories", []) or []:
                    hay = " ".join(
                        [
                            str(mem.get("title", "")),
                            str(mem.get("content", "")),
                            str(mem.get("category", "")),
                            " ".join(mem.get("tags", []) or []),
                        ]
                    ).lower()
                    if q in hay:
                        mems.append(mem)

                # Sort by importance desc, then updated_at desc
                def _sort_key(m: Dict[str, Any]):
                    imp = int(m.get("importance", 0) or 0)
                    upd = str(m.get("updated_at", ""))
                    return (-imp, upd)

                mems.sort(key=_sort_key)
                mems = mems[: max(0, top_k)]

                for mem in mems:
                    importance = mem.get("importance", 3) or 3
                    try:
                        score = float(importance) / 5.0
                    except Exception:
                        score = 0.6
                    title = mem.get("title") or mem.get("category") or "memory"
                    snippet = (mem.get("content", "") or "")[:200]
                    results.append(
                        {
                            "id": f"mem:{mem.get('id', '')}",
                            "score": max(0.0, min(1.0, score)),
                            "title": title,
                            "snippet": snippet,
                        }
                    )
            except Exception as e:
                logger.warning(f"Memory alias search failed: {e}")

        # Truncate to top_k overall, highest score first
        results = sorted(results, key=lambda r: r.get("score", 0.0), reverse=True)[
            : max(0, top_k)
        ]

        payload = {"results": results}
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(payload))]
        )

    async def _alias_fetch(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Alias `fetch` → return full document by id from search results.

        Accepts ids with prefixes: 'lit:' (Chroma) or 'mem:' (PCS memory).
        Returns JSON: { "document": {"id","text","metadata"} }
        """
        raw_id = arguments.get("id") or ""
        if not isinstance(raw_id, str) or ":" not in raw_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"error": "Invalid id. Expected 'lit:...' or 'mem:...'"}
                        ),
                    )
                ],
                isError=True,
            )

        kind, inner_id = raw_id.split(":", 1)
        doc: Dict[str, Any] = {"id": raw_id, "text": "", "metadata": {}}

        try:
            if kind == "lit" and getattr(self.rag_system, "lit_collection", None):
                col = self.rag_system.lit_collection
                res = await asyncio.to_thread(
                    col.get, ids=[inner_id], include=["documents", "metadatas"]
                )
                docs = res.get("documents") or []
                metas = res.get("metadatas") or []
                if docs:
                    doc["text"] = docs[0]
                if metas:
                    doc["metadata"] = metas[0] or {}
            elif kind == "mem":
                try:
                    from scripts.memory_manager import PCSMemoryManager  # type: ignore

                    mgr = PCSMemoryManager()
                    found = None
                    for m in getattr(mgr, "memories", []) or []:
                        if str(m.get("id")) == inner_id:
                            found = m
                            break
                    if found:
                        doc["text"] = found.get("content", "")
                        meta = found.copy()
                        meta.pop("content", None)
                        doc["metadata"] = meta
                except Exception as e:
                    logger.warning(f"Fetch mem error: {e}")
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps({"error": f"Unknown id kind: {kind}"}),
                        )
                    ],
                    isError=True,
                )

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({"document": doc}))]
            )

        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Fetch failed: {str(e)}")],
                isError=True,
            )

    async def _search_literature(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Search literature using RAG++ system."""
        if not self.rag_system:
            await self._initialize_rag_system()

        if not self.rag_system:
            return CallToolResult(
                content=[TextContent(type="text", text="RAG++ system not available")],
                isError=True,
            )

        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 10)
        search_type = arguments.get("search_type", "hybrid")

        try:
            if search_type == "hybrid":
                results = await asyncio.to_thread(
                    self.rag_system.hybrid_search, query, max_results
                )
            elif search_type == "literature":
                results = await asyncio.to_thread(
                    self.rag_system.literature_search, query, max_results
                )
            elif search_type == "memory":
                results = await asyncio.to_thread(
                    self.rag_system.memory_search, query, max_results
                )
            else:
                raise ValueError(f"Unknown search type: {search_type}")

            # Format results
            formatted_results = {
                "query": query,
                "search_type": search_type,
                "results": results,
                "total_found": len(results) if results else 0,
            }

            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=json.dumps(formatted_results, indent=2)
                    )
                ]
            )

        except Exception as e:
            logger.error(f"Search error: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Search failed: {str(e)}")],
                isError=True,
            )

    async def _store_research_finding(
        self, arguments: Dict[str, Any]
    ) -> CallToolResult:
        """Store a research finding."""
        if not self.rag_system:
            await self._initialize_rag_system()

        if not self.rag_system:
            return CallToolResult(
                content=[TextContent(type="text", text="RAG++ system not available")],
                isError=True,
            )

        title = arguments.get("title", "")
        content = arguments.get("content", "")
        source = arguments.get("source", "manual_entry")
        metadata = arguments.get("metadata", {})

        try:
            result = await asyncio.to_thread(
                self.rag_system.store_memory,
                f"{title}\n\n{content}",
                metadata={"source": source, **metadata},
            )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Research finding stored successfully: {title}",
                    )
                ]
            )

        except Exception as e:
            logger.error(f"Storage error: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Storage failed: {str(e)}")],
                isError=True,
            )

    async def _get_recent_findings(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get recent research findings."""
        if not self.rag_system:
            await self._initialize_rag_system()

        if not self.rag_system:
            return CallToolResult(
                content=[TextContent(type="text", text="RAG++ system not available")],
                isError=True,
            )

        limit = arguments.get("limit", 20)
        category = arguments.get("category")

        try:
            # Search for recent findings
            query = "recent research findings"
            if category:
                query += f" {category}"

            results = await asyncio.to_thread(
                self.rag_system.hybrid_search, query, limit
            )

            formatted_results = {
                "recent_findings": results,
                "total_count": len(results) if results else 0,
                "category_filter": category,
            }

            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=json.dumps(formatted_results, indent=2)
                    )
                ]
            )

        except Exception as e:
            logger.error(f"Recent findings error: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"Failed to get recent findings: {str(e)}"
                    )
                ],
                isError=True,
            )

    async def _collect_new_research(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Collect new research papers."""
        if not self.research_collector:
            await self._initialize_rag_system()

        if not self.research_collector:
            return CallToolResult(
                content=[
                    TextContent(type="text", text="Research collector not available")
                ],
                isError=True,
            )

        topics = arguments.get("topics", [])
        years = arguments.get("years", [2023, 2024, 2025])
        max_papers = arguments.get("max_papers", 50)

        try:
            results = []
            for topic in topics:
                papers = await asyncio.to_thread(
                    self.research_collector.search_and_collect, topic, years, max_papers
                )
                results.extend(papers)

            # Store collected papers in RAG system
            if self.rag_system and results:
                for paper in results:
                    await asyncio.to_thread(
                        self.rag_system.store_literature,
                        paper.get("content", ""),
                        paper,
                    )

            collection_summary = {
                "topics_searched": topics,
                "years": years,
                "papers_collected": len(results),
                "papers": results[:10],  # Return first 10 for preview
            }

            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=json.dumps(collection_summary, indent=2)
                    )
                ]
            )

        except Exception as e:
            logger.error(f"Collection error: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Collection failed: {str(e)}")],
                isError=True,
            )

    async def _synthesize_knowledge(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Synthesize knowledge on a topic."""
        if not self.rag_system:
            await self._initialize_rag_system()

        if not self.rag_system:
            return CallToolResult(
                content=[TextContent(type="text", text="RAG++ system not available")],
                isError=True,
            )

        topic = arguments.get("topic", "")
        focus_areas = arguments.get("focus_areas", [])

        try:
            # Search for relevant papers
            search_query = topic
            if focus_areas:
                search_query += " " + " ".join(focus_areas)

            results = await asyncio.to_thread(
                self.rag_system.hybrid_search, search_query, 20
            )

            # Create synthesis
            synthesis = {
                "topic": topic,
                "focus_areas": focus_areas,
                "sources_analyzed": len(results) if results else 0,
                "key_findings": results[:5] if results else [],
                "synthesis_summary": f"Analysis of {len(results) if results else 0} sources on {topic}",
            }

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(synthesis, indent=2))]
            )

        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Synthesis failed: {str(e)}")],
                isError=True,
            )

    async def _store_chat_context(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Store ChatGPT/Gemini conversation in Extended Memory (fallback to simple file)."""
        title = arguments.get("conversation_title") or "Session"
        messages = arguments.get("messages") or []
        context_summary = arguments.get("context_summary") or ""
        try:
            importance = float(arguments.get("importance_score", 0.7) or 0.7)
        except Exception:
            importance = 0.7

        if not isinstance(messages, list) or not messages:
            return CallToolResult(
                content=[TextContent(type="text", text="Missing 'messages' array")],
                isError=True,
            )

        # Try ExtendedMemoryService first
        try:
            from ragpp.extended_memory_service import get_memory_service  # type: ignore

            memory_service = get_memory_service()
            conversation_data = {
                "messages": messages,
                "summary": context_summary,
                "source": "mcp",
            }

            conv_id = await asyncio.to_thread(
                memory_service.store_conversation,
                conversation_data,
                title,
                importance,
            )

            # Store assistant insights as individual memories (best-effort)
            for idx, msg in enumerate(messages):
                try:
                    if (
                        isinstance(msg, dict)
                        and msg.get("role") == "assistant"
                        and len(msg.get("content", "")) > 100
                    ):
                        await asyncio.to_thread(
                            memory_service.store_memory,
                            content=msg["content"],
                            memory_type="chatgpt_insight",
                            tags=["chat", "insight", title],
                            metadata={
                                "conversation_id": conv_id,
                                "message_index": idx,
                                "source": "mcp",
                            },
                            importance_score=max(0.0, min(1.0, importance * 0.8)),
                        )
                except Exception:
                    pass

            payload = {"status": "stored", "conversation_id": conv_id}
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(payload))]
            )

        except Exception as e:
            logger.warning(f"ExtendedMemoryService unavailable, fallback in use: {e}")

        # Fallback: file-based memory manager
        try:
            from scripts.memory_manager import PCSMemoryManager  # type: ignore

            mgr = PCSMemoryManager()
            # Flatten messages for content
            flat = []
            for m in messages:
                if isinstance(m, dict):
                    flat.append(f"{m.get('role','unknown')}: {m.get('content','')}")
                else:
                    flat.append(str(m))
            content = (
                f"Conversation summary: {context_summary}\n\n" + "\n".join(flat)
            )
            mem_id = mgr.add_memory(
                title=title,
                content=content,
                category="chat_context",
                importance=int(round(importance * 5)) or 3,
                tags=["mcp", "chat", "context"],
            )
            payload = {"status": "stored_fallback", "memory_id": mem_id}
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(payload))]
            )
        except Exception as e:
            logger.error(f"Fallback memory store failed: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Store failed: {str(e)}")],
                isError=True,
            )

    async def _recall_context(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Recall relevant context from Extended Memory Service."""
        query = arguments.get("query", "")
        include_conversations = bool(arguments.get("include_conversations", True))
        include_insights = bool(arguments.get("include_insights", True))
        try:
            max_results = int(arguments.get("max_results", 10) or 10)
        except Exception:
            max_results = 10

        try:
            from ragpp.extended_memory_service import get_memory_service  # type: ignore

            memory_service = get_memory_service()
            memory_types = []
            if include_conversations:
                memory_types.append("conversation")
            if include_insights:
                memory_types.extend(["chatgpt_insight", "insight", "context"])

            results = await asyncio.to_thread(
                memory_service.search_memory,
                query=query,
                memory_types=memory_types if memory_types else None,
                max_results=max_results,
                importance_threshold=0.4,
            )

            # Format succinct JSON
            formatted = {
                "query": query,
                "total": len(results),
                "results": [
                    {
                        "content": r.get("content", ""),
                        "type": r.get("memory_type", ""),
                        "relevance": r.get("relevance_score", 0.0),
                        "timestamp": r.get("timestamp", ""),
                        "tags": r.get("tags", []),
                    }
                    for r in results
                ],
            }

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(formatted))]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Recall failed: {str(e)}")],
                isError=True,
            )

    async def _get_database_status(self) -> Dict[str, Any]:
        """Get database status."""
        if not self.rag_system:
            return {"status": "not_initialized", "error": "RAG++ system not available"}

        try:
            # Get basic status information
            status = {
                "status": "healthy",
                "system_initialized": True,
                "database_path": getattr(self.rag_system, "db_path", "unknown"),
                "capabilities": [
                    "hybrid_search",
                    "literature_search",
                    "memory_search",
                    "knowledge_storage",
                    "research_collection",
                ],
            }

            # Try to get collection info
            try:
                collection = self.rag_system.literature_collection
                if collection:
                    status["indexed_documents"] = collection.count()
                else:
                    status["indexed_documents"] = 0
            except:
                status["indexed_documents"] = "unknown"

            return status

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _get_indexed_papers(self) -> Dict[str, Any]:
        """Get list of indexed papers."""
        if not self.rag_system:
            return {"papers": [], "total": 0}

        try:
            # Search for all papers
            results = await asyncio.to_thread(
                self.rag_system.literature_search, "", 100
            )

            papers = []
            for result in results[:50]:  # Limit to 50 for performance
                papers.append(
                    {
                        "content_preview": result[:200] + "..."
                        if len(result) > 200
                        else result,
                        "length": len(result),
                    }
                )

            return {
                "papers": papers,
                "total_shown": len(papers),
                "total_available": len(results) if results else 0,
            }

        except Exception as e:
            return {"papers": [], "error": str(e)}

    async def _get_system_config(self) -> Dict[str, Any]:
        """Get system configuration."""
        return {
            "server_name": "ragpp-mcp-server",
            "version": "1.0.0",
            "protocol": "Model Context Protocol (MCP)",
            "capabilities": {
                "tools": [
                    "search_literature",
                    "store_research_finding",
                    "get_recent_findings",
                    "collect_new_research",
                    "synthesize_knowledge",
                ],
                "resources": [
                    "database_status",
                    "indexed_papers",
                    "system_config",
                    "recent_findings",
                ],
                "search_types": ["hybrid", "literature", "memory"],
                "research_domains": [
                    "psychiatry",
                    "computational_psychiatry",
                    "digital_phenotyping",
                    "machine_learning",
                ],
            },
            "system_status": "operational" if self.rag_system else "initializing",
        }


async def main():
    """Main server function."""
    server_instance = RAGPlusMCPServer()

    # Initialize the RAG system
    await server_instance._initialize_rag_system()

    # Run the server using stdio
    from mcp import StdioServerParameters

    stdio_params = StdioServerParameters()
    await server_instance.server.run(
        stdio_params.read_stream,
        stdio_params.write_stream,
        stdio_params.initialization_options,
    )


if __name__ == "__main__":
    asyncio.run(main())
