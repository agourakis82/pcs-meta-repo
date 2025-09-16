"""Darwin Platform RAG++ Router

Enhanced Research Agent endpoints with long-horizon reasoning,
scientific discovery, and iterative search capabilities.

Endpoints:
- POST /rag-plus/query - Simple RAG query
- POST /rag-plus/iterative - Iterative reasoning query  
- POST /rag-plus/discovery - Trigger discovery update
- GET /rag-plus/status - Service status
- POST /rag-plus/discovery/start - Start continuous discovery
- POST /rag-plus/discovery/stop - Stop continuous discovery
- GET /rag-plus/sources - List discovery sources
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from api.security import require_api_key, rate_limit
from services.rag_plus import DarwinRAGPlusService, get_rag_plus_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/rag-plus",
    tags=["RAG++ Enhanced Research"],
    dependencies=[Depends(require_api_key), Depends(rate_limit)],
)


# Request/Response Models
class RAGPlusQuery(BaseModel):
    """RAG++ query request"""
    query: str = Field(..., description="Research question or query")
    top_k: Optional[int] = Field(None, description="Number of documents to retrieve")
    include_sources: bool = Field(True, description="Include source information")


class RAGPlusResponse(BaseModel):
    """RAG++ query response"""
    answer: str = Field(..., description="Generated answer")
    sources: List[Dict[str, Any]] = Field(
        default_factory=list, description="Source documents"
    )
    method: str = Field(..., description="Processing method used")
    retrieved_docs: Optional[int] = Field(
        None, description="Number of documents retrieved"
    )
    reasoning_steps: Optional[List[Dict[str, Any]]] = Field(
        None, description="Reasoning steps for iterative queries"
    )
    total_steps: Optional[int] = Field(None, description="Total reasoning steps")


class DiscoveryResponse(BaseModel):
    """Discovery operation response"""
    status: str = Field(..., description="Operation status")
    fetched: int = Field(..., description="Articles fetched")
    novel: int = Field(..., description="Novel articles found")
    added: int = Field(..., description="Articles added to knowledge base")
    errors: int = Field(..., description="Errors encountered")


class ServiceStatus(BaseModel):
    """RAG++ service status"""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    components: Dict[str, Any] = Field(..., description="Component status")
    configuration: Dict[str, Any] = Field(..., description="Service configuration")
    timestamp: str = Field(..., description="Status timestamp")


class DocumentAdd(BaseModel):
    """Add document to knowledge base"""
    content: str = Field(..., description="Document content")
    source: str = Field("", description="Document source")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


@router.post("/query", response_model=RAGPlusResponse)
async def query_rag_plus(
    request: RAGPlusQuery,
    service: DarwinRAGPlusService = Depends(get_rag_plus_service)
):
    """
    Query RAG++ system with simple retrieval-augmented generation.
    
    Uses semantic search to find relevant documents and generates
    an answer with citations from the Darwin knowledge base.
    """
    try:
        logger.info(f"RAG++ query: {request.query[:100]}...")
        
        result = await service.answer_question(request.query)
        
        # Filter sources if not requested
        if not request.include_sources:
            result["sources"] = []
        
        return RAGPlusResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in RAG++ query: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/iterative", response_model=RAGPlusResponse)
async def query_iterative(
    request: RAGPlusQuery,
    service: DarwinRAGPlusService = Depends(get_rag_plus_service)
):
    """
    Query RAG++ system with iterative ReAct reasoning.
    
    Uses Thought→Action→Observation loops for complex questions
    requiring multi-step reasoning and information gathering.
    """
    try:
        logger.info(f"RAG++ iterative query: {request.query[:100]}...")
        
        result = await service.answer_question_iterative(request.query)
        
        # Filter sources if not requested
        if not request.include_sources and "sources" in result:
            result["sources"] = []
        
        return RAGPlusResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in RAG++ iterative query: {e}")
        raise HTTPException(status_code=500, detail=f"Iterative query failed: {str(e)}")


@router.post("/discovery", response_model=DiscoveryResponse)
async def trigger_discovery(
    background_tasks: BackgroundTasks,
    service: DarwinRAGPlusService = Depends(get_rag_plus_service)
):
    """
    Trigger scientific discovery update.
    
    Scans configured RSS feeds for new articles, performs novelty
    detection, and adds relevant discoveries to the knowledge base.
    """
    try:
        logger.info("Triggering RAG++ discovery update")
        
        # Run discovery in background to avoid timeout
        stats = await service.discover_new_knowledge()
        
        return DiscoveryResponse(
            status="completed",
            fetched=stats.get("fetched", 0),
            novel=stats.get("novel", 0),
            added=stats.get("added", 0),
            errors=stats.get("errors", 0)
        )
        
    except Exception as e:
        logger.error(f"Error in RAG++ discovery: {e}")
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@router.get("/status", response_model=ServiceStatus)
async def get_service_status(
    service: DarwinRAGPlusService = Depends(get_rag_plus_service)
):
    """
    Get comprehensive RAG++ service status.
    
    Returns health information for all components including
    BigQuery, Vertex AI models, and discovery monitoring.
    """
    try:
        status = await service.get_service_status()
        return ServiceStatus(**status)
        
    except Exception as e:
        logger.error(f"Error getting RAG++ status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/discovery/start")
async def start_continuous_discovery(
    service: DarwinRAGPlusService = Depends(get_rag_plus_service)
):
    """
    Start continuous scientific discovery monitoring.
    
    Begins 24/7 monitoring of scientific sources with automatic
    knowledge base updates for novel discoveries.
    """
    try:
        await service.start_continuous_discovery()
        return {
            "status": "started",
            "message": "Continuous discovery monitoring started",
            "interval_seconds": service.config.discovery_interval
        }
        
    except Exception as e:
        logger.error(f"Error starting RAG++ discovery: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start discovery: {str(e)}")


@router.post("/discovery/stop")
async def stop_continuous_discovery(
    service: DarwinRAGPlusService = Depends(get_rag_plus_service)
):
    """
    Stop continuous scientific discovery monitoring.
    
    Stops the background discovery process while preserving
    the existing knowledge base.
    """
    try:
        await service.stop_continuous_discovery()
        return {
            "status": "stopped",
            "message": "Continuous discovery monitoring stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping RAG++ discovery: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop discovery: {str(e)}")


@router.get("/sources")
async def list_discovery_sources(
    service: DarwinRAGPlusService = Depends(get_rag_plus_service)
):
    """
    List configured scientific discovery sources.
    
    Returns information about RSS feeds and other sources
    monitored for scientific discoveries.
    """
    try:
        sources = []
        for source in service.sources:
            sources.append({
                "name": source.name,
                "type": source.type,
                "url": source.url,
                "enabled": source.enabled,
                "check_interval": source.check_interval
            })
        
        return {
            "sources": sources,
            "total_sources": len(sources),
            "enabled_sources": len([s for s in service.sources if s.enabled]),
            "discovery_enabled": service.config.discovery_enabled
        }
        
    except Exception as e:
        logger.error(f"Error listing RAG++ sources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sources: {str(e)}")


@router.post("/documents")
async def add_document(
    request: DocumentAdd,
    service: DarwinRAGPlusService = Depends(get_rag_plus_service)
):
    """
    Add document to RAG++ knowledge base.
    
    Manually add a document with content and metadata to the
    Darwin knowledge base for use in future queries.
    """
    try:
        import hashlib

        # Generate document ID
        doc_id = hashlib.md5(request.content.encode()).hexdigest()
        
        success = await service.add_document(
            doc_id=doc_id,
            content=request.content,
            source=request.source,
            metadata=request.metadata,
            discovery_type="manual_addition"
        )
        
        if success:
            return {
                "status": "added",
                "document_id": doc_id,
                "message": "Document added to knowledge base successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add document")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")


@router.get("/search")
async def search_knowledge_base(
    query: str,
    top_k: int = 5,
    service: DarwinRAGPlusService = Depends(get_rag_plus_service)
):
    """
    Search RAG++ knowledge base directly.
    
    Performs semantic search without answer generation,
    returning the most relevant documents with similarity scores.
    """
    try:
        results = await service.query_knowledge_base(query, top_k=top_k)
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/config")
async def get_configuration(
    service: DarwinRAGPlusService = Depends(get_rag_plus_service)
):
    """
    Get RAG++ service configuration.
    
    Returns current configuration parameters including
    models, thresholds, and discovery settings.
    """
    try:
        return {
            "project_id": service.config.project_id,
            "location": service.config.location,
            "dataset_id": service.config.dataset_id,
            "table_id": service.config.table_id,
            "embedding_model": service.config.embedding_model,
            "generation_model": service.config.generation_model,
            "novelty_threshold": service.config.novelty_threshold,
            "max_iterations": service.config.max_iterations,
            "top_k_retrieval": service.config.top_k_retrieval,
            "discovery_enabled": service.config.discovery_enabled,
            "discovery_interval": service.config.discovery_interval
        }
        
    except Exception as e:
        logger.error(f"Error getting RAG++ config: {e}")
        raise HTTPException(
            status_code=500, detail=f"Config retrieval failed: {str(e)}"
        )


# Health check endpoint for monitoring
@router.get("/health")
async def health_check(
    service: DarwinRAGPlusService = Depends(get_rag_plus_service)
):
    """
    Quick health check for RAG++ service.
    
    Returns basic health status without comprehensive testing.
    Use /status for detailed health information.
    """
    try:
        # Quick test
        test_result = await service.get_embedding("health check")
        healthy = len(test_result) > 0
        
        return {
            "healthy": healthy,
            "service": "rag_plus",
            "message": (
                "RAG++ service is operational" 
                if healthy else "RAG++ service degraded"
            )
        }
        
    except Exception as e:
        logger.error(f"RAG++ health check failed: {e}")
        return {
            "healthy": False,
            "service": "rag_plus",
            "message": f"RAG++ service error: {str(e)}",
        }
