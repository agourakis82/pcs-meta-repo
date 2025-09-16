#!/usr/bin/env python3
"""
Memory Management API Endpoints
Endpoints adicionais para gerenciamento da memória extendida.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from extended_memory_service import get_memory_service

# Create router
memory_router = APIRouter(prefix="/memory", tags=["memory"])

# Request models
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

# Memory service dependency
def get_memory():
    return get_memory_service()

@memory_router.post("/store")
async def store_memory(request: StoreMemoryRequest, memory_service = Depends(get_memory)):
    """Armazena uma nova memória."""
    try:
        memory_id = memory_service.store_memory(
            content=request.content,
            memory_type=request.memory_type,
            tags=request.tags,
            metadata=request.metadata,
            importance_score=request.importance_score
        )
        return {"memory_id": memory_id, "status": "stored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.post("/store/conversation")
async def store_conversation(request: StoreConversationRequest, memory_service = Depends(get_memory)):
    """Armazena uma conversa completa."""
    try:
        conv_id = memory_service.store_conversation(
            conversation_data=request.conversation_data,
            title=request.title,
            importance_score=request.importance_score
        )
        return {"conversation_id": conv_id, "status": "stored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.post("/store/project")
async def store_project_context(request: StoreProjectContextRequest, memory_service = Depends(get_memory)):
    """Armazena contexto do projeto."""
    try:
        context_id = memory_service.store_project_context(
            project_name=request.project_name,
            context_type=request.context_type,
            content=request.content,
            metadata=request.metadata
        )
        return {"context_id": context_id, "status": "stored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.post("/search")
async def search_memory(request: SearchMemoryRequest, memory_service = Depends(get_memory)):
    """Busca na memória usando busca semântica."""
    try:
        results = memory_service.search_memory(
            query=request.query,
            memory_types=request.memory_types,
            max_results=request.max_results,
            importance_threshold=request.importance_threshold
        )
        return {"query": request.query, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/recent")
async def get_recent_memories(
    days: int = 7,
    memory_types: Optional[str] = None,
    max_results: int = 20,
    memory_service = Depends(get_memory)
):
    """Recupera memórias recentes."""
    try:
        types_list = memory_types.split(',') if memory_types else None
        results = memory_service.get_recent_memories(
            days=days,
            memory_types=types_list,
            max_results=max_results
        )
        return {"recent_memories": results, "count": len(results), "days": days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/project/status")
async def get_project_status(
    project_name: str = "pcs-meta-repo",
    memory_service = Depends(get_memory)
):
    """Recupera status do projeto."""
    try:
        status = memory_service.get_project_status(project_name)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/stats")
async def get_memory_stats(memory_service = Depends(get_memory)):
    """Estatísticas do serviço de memória."""
    try:
        stats = memory_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.post("/backup")
async def create_backup(memory_service = Depends(get_memory)):
    """Cria backup da memória."""
    try:
        backup_path = memory_service.create_backup()
        return {"backup_path": backup_path, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.post("/cleanup")
async def cleanup_memories(days_to_keep: int = 90, memory_service = Depends(get_memory)):
    """Limpa memórias antigas."""
    try:
        deleted_count = memory_service.cleanup_old_memories(days_to_keep)
        return {"deleted_count": deleted_count, "days_kept": days_to_keep}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ChatGPT integration endpoints
@memory_router.post("/chatgpt/context")
async def store_chatgpt_context(
    conversation_title: str,
    messages: List[Dict[str, str]],
    context_summary: str = "",
    importance_score: float = 0.7,
    memory_service = Depends(get_memory)
):
    """Armazena contexto de conversa do ChatGPT."""
    try:
        # Store as conversation
        conversation_data = {
            "messages": messages,
            "summary": context_summary,
            "source": "chatgpt",
            "timestamp": datetime.now().isoformat()
        }
        
        conv_id = memory_service.store_conversation(
            conversation_data=conversation_data,
            title=conversation_title,
            importance_score=importance_score
        )
        
        # Also store key insights as individual memories
        for i, msg in enumerate(messages):
            if msg.get('role') == 'assistant' and len(msg.get('content', '')) > 100:
                memory_service.store_memory(
                    content=msg['content'],
                    memory_type="chatgpt_insight",
                    tags=["chatgpt", "insight", conversation_title],
                    metadata={
                        "conversation_id": conv_id,
                        "message_index": i,
                        "source": "chatgpt"
                    },
                    importance_score=importance_score * 0.8
                )
        
        return {
            "conversation_id": conv_id,
            "status": "stored",
            "message_count": len(messages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/chatgpt/recall")
async def recall_context(
    query: str,
    include_conversations: bool = True,
    include_insights: bool = True,
    max_results: int = 10,
    memory_service = Depends(get_memory)
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
            importance_threshold=0.4
        )
        
        # Format for ChatGPT consumption
        context_summary = []
        for result in results:
            context_summary.append({
                "content": result['content'][:500] + "..." if len(result['content']) > 500 else result['content'],
                "type": result['memory_type'],
                "relevance": result['relevance_score'],
                "timestamp": result['timestamp'],
                "tags": result['tags']
            })
        
        return {
            "query": query,
            "context": context_summary,
            "total_results": len(results),
            "summary": f"Found {len(results)} relevant memories for your query."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
