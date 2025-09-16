"""Darwin Platform RAG Router

Vertex-native RAG endpoints with Engine and Vector Search backends.
Provides retrieval and answer generation with citations.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from api.security import rate_limit, require_api_key
from services.rag_vertex import get_rag
from services.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
    dependencies=[Depends(require_api_key), Depends(rate_limit)],
)


class RagRequest(BaseModel):
    """RAG request model."""

    query: str = Field(..., description="Query text")
    k: Optional[int] = Field(5, ge=1, le=20, description="Number of sources")


class RagSource(BaseModel):
    """RAG source model."""

    title: str = Field(..., description="Source title")
    snippet: str = Field(..., description="Source snippet")
    url_or_doi: Optional[str] = Field(None, description="Source URL or DOI")
    score: float = Field(..., description="Relevance score")


class RagResponse(BaseModel):
    """RAG response model."""

    text: str = Field(..., description="Generated answer text")
    sources: List[RagSource] = Field(..., description="Source citations")


@router.post("", response_model=RagResponse)
async def rag_query(request: RagRequest, response: Response) -> RagResponse:
    """
    Generate answer with citations using RAG.

    Args:
        request: RAG query request
        response: FastAPI response for headers

    Returns:
        Answer with source citations
    """
    try:
        rag_backend = get_rag()
        k_value = request.k if request.k is not None else 5
        rag_result = await rag_backend.answer(request.query, k_value)

        # Set response headers
        response.headers["X-RAG-Backend"] = rag_result.backend_type
        response.headers["X-RAG-Cache"] = "HIT" if rag_result.cache_hit else "MISS"

        # Check for context caching
        settings = get_settings()
        if settings.CONTEXT_CACHE_ENABLED:
            response.headers["X-Context-Cache"] = "ENABLED"

        # Convert to response model
        sources = [
            RagSource(
                title=source.title,
                snippet=source.snippet,
                url_or_doi=source.url_or_doi,
                score=source.score,
            )
            for source in rag_result.sources
        ]

        return RagResponse(text=rag_result.text, sources=sources)

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail="RAG query processing failed")


@router.get("/retrieve", response_model=List[RagSource])
async def rag_retrieve(
    response: Response,
    q: str = Query(..., description="Query text"),
    k: int = Query(5, ge=1, le=20, description="Number of sources"),
) -> List[RagSource]:
    """
    Retrieve relevant sources without answer generation.

    Args:
        q: Query text
        k: Number of sources to retrieve
        response: FastAPI response for headers

    Returns:
        List of relevant sources
    """
    try:
        rag_backend = get_rag()
        rag_result = await rag_backend.retrieve(q, k)

        # Set response headers
        if response:
            response.headers["X-RAG-Backend"] = rag_result.backend_type
            response.headers["X-RAG-Cache"] = "HIT" if rag_result.cache_hit else "MISS"

        # Convert to response model
        sources = [
            RagSource(
                title=source.title,
                snippet=source.snippet,
                url_or_doi=source.url_or_doi,
                score=source.score,
            )
            for source in rag_result.sources
        ]

        return sources

    except Exception as e:
        logger.error(f"RAG retrieve failed: {e}")
        raise HTTPException(status_code=500, detail="RAG retrieval failed")
