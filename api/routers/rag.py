"""RAG router for retrieval-augmented generation endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_api_key
from ..logging import get_logger
from ..models import RAGAnswer, RAGQuery
from ..rate_limit import rate_limit_dependency
from services.rag_service import rag_service

logger = get_logger("rag_router")

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=RAGAnswer)
async def query_documents(
    query: RAGQuery,
    api_key: str = Depends(require_api_key),
    _rate_limit: None = Depends(rate_limit_dependency)
):
    """
    Query documents using RAG (Retrieval-Augmented Generation).
    
    Searches the document collection and generates an answer based on
    retrieved context and the user's query.
    """
    logger.info("RAG query received", query=query.query)
    
    try:
        result = await rag_service.query(query)
        logger.info("RAG query completed", sources_count=len(result.sources))
        return result
        
    except Exception as e:
        logger.error("RAG query failed", error=str(e))
        raise HTTPException(status_code=500, detail="Query processing failed")


@router.get("/health")
async def rag_health():
    """Get RAG service health status."""
    try:
        health = await rag_service.health_check()
        return health
    except Exception as e:
        logger.error("RAG health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")