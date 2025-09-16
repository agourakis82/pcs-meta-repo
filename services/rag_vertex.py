"""
Vertex AI RAG Backend Implementation

Provides two RAG backends:
1. VertexRagEngineBackend: Uses Vertex AI RAG Engine with corpora
2. VertexVectorBackend: Uses Vector Search with MatchingEngineIndexEndpoint

Both backends return structured responses with citations and caching.
"""

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from services.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class RagSource:
    """RAG source citation."""

    title: str
    snippet: str
    url_or_doi: Optional[str] = None
    score: float = 0.0


@dataclass
class RagResponse:
    """RAG response with text and sources."""

    text: str
    sources: List[RagSource]
    backend_type: str
    cache_hit: bool = False


class RagBackend(ABC):
    """Abstract RAG backend interface."""

    @abstractmethod
    async def retrieve(self, query: str, k: int = 5) -> RagResponse:
        """Retrieve relevant documents for query."""
        pass

    @abstractmethod
    async def answer(self, query: str, k: int = 5) -> RagResponse:
        """Generate answer with citations for query."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check backend health."""
        pass


class VertexRagEngineBackend(RagBackend):
    """Vertex AI RAG Engine backend using corpora."""

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._client = None
        self._cache = {}

    def _get_client(self):
        """Get or create Vertex AI client."""
        if self._client is None:
            try:
                import vertexai
                from vertexai import preview

                vertexai.init(
                    project=self.settings.GCP_PROJECT,
                    location=self.settings.GCP_LOCATION,
                )
                self._client = preview.rag.rag_retrieval_tool.RagRetrievalTool()
            except ImportError:
                logger.error("Vertex AI SDK not available")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Vertex RAG client: {e}")
                raise
        return self._client

    def _cache_key(self, query: str, k: int) -> str:
        """Generate cache key for query."""
        key_str = f"{query}:{k}:{self.settings.RAG_CORPUS}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[RagResponse]:
        """Get response from cache if valid."""
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.settings.RAG_CACHE_TTL:
                cached_data.cache_hit = True
                return cached_data
            else:
                del self._cache[cache_key]
        return None

    def _store_in_cache(self, cache_key: str, response: RagResponse):
        """Store response in cache."""
        if len(self._cache) >= self.settings.RAG_CACHE_SIZE:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        response.cache_hit = False
        self._cache[cache_key] = (response, time.time())

    async def retrieve(self, query: str, k: int = 5) -> RagResponse:
        """Retrieve documents using RAG Engine."""
        cache_key = self._cache_key(query, k)

        # Check cache first
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            return cached_response

        try:
            client = self._get_client()

            # Use RAG Engine retrieval
            response = await client.retrieve_async(
                corpus_id=self.settings.RAG_CORPUS, query=query, similarity_top_k=k
            )

            sources = []
            for doc in response.documents:
                source = RagSource(
                    title=doc.metadata.get("title", "Unknown"),
                    snippet=doc.text[:500],  # Truncate snippet
                    url_or_doi=doc.metadata.get("url") or doc.metadata.get("doi"),
                    score=doc.score,
                )
                sources.append(source)

            rag_response = RagResponse(
                text="",  # retrieve doesn't generate text
                sources=sources,
                backend_type="engine",
            )

            # Cache the response
            self._store_in_cache(cache_key, rag_response)

            return rag_response

        except Exception as e:
            logger.error(f"RAG Engine retrieval failed: {e}")
            return RagResponse(text="", sources=[], backend_type="engine")

    async def answer(self, query: str, k: int = 5) -> RagResponse:
        """Generate answer using RAG Engine."""
        try:
            # First retrieve relevant documents
            retrieval_response = await self.retrieve(query, k)

            if not retrieval_response.sources:
                return RagResponse(
                    text="I couldn't find relevant information to answer your question.",
                    sources=[],
                    backend_type="engine",
                    cache_hit=retrieval_response.cache_hit,
                )

            # Generate answer using Gemini with retrieved context
            from vertexai.generative_models import GenerativeModel

            model = GenerativeModel(self.settings.GEMINI_ANSWER_MODEL)

            # Build context from sources
            context_parts = []
            for i, source in enumerate(retrieval_response.sources):
                context_parts.append(f"[{i+1}] {source.snippet}")

            context = "\n\n".join(context_parts)

            # Stable prefix for context caching
            stable_prefix = """You are Darwin, an expert research assistant. 
Answer questions using the provided context and cite sources with [n] notation.
Be precise, comprehensive, and include relevant citations.

Context:
"""

            prompt = f"{stable_prefix}\n{context}\n\nQuestion: {query}\n\nAnswer:"

            response = await model.generate_content_async(prompt)
            answer_text = response.text

            return RagResponse(
                text=answer_text,
                sources=retrieval_response.sources,
                backend_type="engine",
                cache_hit=retrieval_response.cache_hit,
            )

        except Exception as e:
            logger.error(f"RAG Engine answer generation failed: {e}")
            return RagResponse(
                text="I encountered an error while generating the answer.",
                sources=[],
                backend_type="engine",
            )

    async def health_check(self) -> bool:
        """Check RAG Engine health."""
        try:
            client = self._get_client()
            # Simple test query
            test_response = await client.retrieve_async(
                corpus_id=self.settings.RAG_CORPUS, query="test", similarity_top_k=1
            )
            return True
        except Exception as e:
            logger.warning(f"RAG Engine health check failed: {e}")
            return False


class VertexVectorBackend(RagBackend):
    """Vertex Vector Search backend using MatchingEngineIndexEndpoint."""

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._client = None
        self._embedding_client = None
        self._cache = {}

    def _get_clients(self):
        """Get or create Vector Search and embedding clients."""
        if self._client is None:
            try:
                from google.cloud import aiplatform

                aiplatform.init(
                    project=self.settings.GCP_PROJECT,
                    location=self.settings.GCP_LOCATION,
                )

                self._client = aiplatform.MatchingEngineIndexEndpoint(
                    self.settings.VS_INDEX_ENDPOINT
                )

                # Initialize embedding client
                from vertexai.language_models import TextEmbeddingModel

                self._embedding_client = TextEmbeddingModel.from_pretrained(
                    self.settings.GEMINI_EMBED_MODEL
                )

            except ImportError:
                logger.error("Google Cloud AI Platform SDK not available")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Vector Search client: {e}")
                raise

        return self._client, self._embedding_client

    def _cache_key(self, query: str, k: int) -> str:
        """Generate cache key for query."""
        key_str = f"{query}:{k}:{self.settings.VS_DEPLOYED_INDEX_ID}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[RagResponse]:
        """Get response from cache if valid."""
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.settings.RAG_CACHE_TTL:
                cached_data.cache_hit = True
                return cached_data
            else:
                del self._cache[cache_key]
        return None

    def _store_in_cache(self, cache_key: str, response: RagResponse):
        """Store response in cache."""
        if len(self._cache) >= self.settings.RAG_CACHE_SIZE:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        response.cache_hit = False
        self._cache[cache_key] = (response, time.time())

    async def retrieve(self, query: str, k: int = 5) -> RagResponse:
        """Retrieve documents using Vector Search."""
        cache_key = self._cache_key(query, k)

        # Check cache first
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            return cached_response

        try:
            client, embedding_client = self._get_clients()

            # Generate query embedding
            embeddings = await embedding_client.get_embeddings_async([query])
            query_embedding = embeddings[0].values

            # Search vector index
            neighbors = await client.find_neighbors_async(
                deployed_index_id=self.settings.VS_DEPLOYED_INDEX_ID,
                queries=[query_embedding],
                num_neighbors=k,
            )

            sources = []
            for neighbor in neighbors[0]:
                # Parse neighbor metadata
                metadata = neighbor.metadata or {}
                source = RagSource(
                    title=metadata.get("title", "Unknown Document"),
                    snippet=metadata.get("text", "")[:500],
                    url_or_doi=metadata.get("url") or metadata.get("doi"),
                    score=neighbor.distance,
                )
                sources.append(source)

            rag_response = RagResponse(
                text="",  # retrieve doesn't generate text
                sources=sources,
                backend_type="vector",
            )

            # Cache the response
            self._store_in_cache(cache_key, rag_response)

            return rag_response

        except Exception as e:
            logger.error(f"Vector Search retrieval failed: {e}")
            return RagResponse(text="", sources=[], backend_type="vector")

    async def answer(self, query: str, k: int = 5) -> RagResponse:
        """Generate answer using Vector Search."""
        try:
            # First retrieve relevant documents
            retrieval_response = await self.retrieve(query, k)

            if not retrieval_response.sources:
                return RagResponse(
                    text="I couldn't find relevant information to answer your question.",
                    sources=[],
                    backend_type="vector",
                    cache_hit=retrieval_response.cache_hit,
                )

            # Generate answer using Gemini with retrieved context
            from vertexai.generative_models import GenerativeModel

            model = GenerativeModel(self.settings.GEMINI_ANSWER_MODEL)

            # Build context from sources
            context_parts = []
            for i, source in enumerate(retrieval_response.sources):
                context_parts.append(f"[{i+1}] {source.snippet}")

            context = "\n\n".join(context_parts)

            # Stable prefix for context caching
            stable_prefix = """You are Darwin, an expert research assistant.
Answer questions using the provided context and cite sources with [n] notation.
Be precise, comprehensive, and include relevant citations.

Context:
"""

            prompt = f"{stable_prefix}\n{context}\n\nQuestion: {query}\n\nAnswer:"

            response = await model.generate_content_async(prompt)
            answer_text = response.text

            return RagResponse(
                text=answer_text,
                sources=retrieval_response.sources,
                backend_type="vector",
                cache_hit=retrieval_response.cache_hit,
            )

        except Exception as e:
            logger.error(f"Vector Search answer generation failed: {e}")
            return RagResponse(
                text="I encountered an error while generating the answer.",
                sources=[],
                backend_type="vector",
            )

    async def health_check(self) -> bool:
        """Check Vector Search health."""
        try:
            client, embedding_client = self._get_clients()

            # Simple test embedding
            test_embeddings = await embedding_client.get_embeddings_async(["test"])

            # Test vector search
            test_neighbors = await client.find_neighbors_async(
                deployed_index_id=self.settings.VS_DEPLOYED_INDEX_ID,
                queries=[test_embeddings[0].values],
                num_neighbors=1,
            )

            return True
        except Exception as e:
            logger.warning(f"Vector Search health check failed: {e}")
            return False


# Factory function
@lru_cache(maxsize=1)
def get_rag() -> RagBackend:
    """
    Get RAG backend based on configuration.

    Returns:
        RagBackend: RAG Engine if RAG_CORPUS is set, else Vector Search
    """
    settings = get_settings()

    if settings.RAG_CORPUS:
        logger.info("Using Vertex RAG Engine backend")
        return VertexRagEngineBackend(settings)
    elif settings.VS_INDEX_ENDPOINT and settings.VS_DEPLOYED_INDEX_ID:
        logger.info("Using Vertex Vector Search backend")
        return VertexVectorBackend(settings)
    else:
        logger.error("No RAG backend configured")
        raise ValueError(
            "Either RAG_CORPUS or both VS_INDEX_ENDPOINT and "
            "VS_DEPLOYED_INDEX_ID must be configured"
        )


# For testing purposes
class MockRagBackend(RagBackend):
    """Mock RAG backend for testing."""

    async def retrieve(self, query: str, k: int = 5) -> RagResponse:
        """Mock retrieve method."""
        sources = [
            RagSource(
                title=f"Document {i}",
                snippet=f"Mock snippet {i} for query: {query}",
                url_or_doi=f"https://example.com/doc{i}",
                score=0.9 - i * 0.1,
            )
            for i in range(1, min(k + 1, 4))
        ]

        return RagResponse(text="", sources=sources, backend_type="mock")

    async def answer(self, query: str, k: int = 5) -> RagResponse:
        """Mock answer method."""
        retrieval_response = await self.retrieve(query, k)

        answer_text = f"Mock answer for: {query}. Based on {len(retrieval_response.sources)} sources."

        return RagResponse(
            text=answer_text, sources=retrieval_response.sources, backend_type="mock"
        )

    async def health_check(self) -> bool:
        """Mock health check."""
        return True
