#!/usr/bin/env python3
"""
Multi-AI Cache System - Endpoints para cache inteligente entre diferentes IAs
Extensão do RAG++ Web Server para gerenciar contexto e conversas entre ChatGPT, Claude, etc.
"""

import json

# Import memory service function
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel

sys.path.append(str(Path(__file__).parent))
try:
    from ragpp.extended_memory_service import get_memory_service

    get_memory = get_memory_service
except ImportError:
    # Fallback function
    def get_memory():
        raise HTTPException(status_code=503, detail="Memory service not available")


# Novos modelos para cache multi-IA
class AISessionRequest(BaseModel):
    """Requisição para criar nova sessão de IA."""

    ai_type: str  # chatgpt, claude, copilot, gemini, etc.
    session_name: str
    context_summary: Optional[str] = ""
    initial_prompt: Optional[str] = ""
    user_id: Optional[str] = "default"
    metadata: Optional[Dict[str, Any]] = {}


class AIContextStore(BaseModel):
    """Modelo para armazenar contexto de conversa de IA."""

    session_id: str
    ai_type: str
    messages: List[Dict[str, str]]  # role, content, timestamp
    context_summary: str
    importance_score: float = 0.5
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}


class CrossAITransfer(BaseModel):
    """Modelo para transferir contexto entre IAs."""

    source_session_id: str
    target_ai_type: str
    transfer_type: str = "full"  # full, summary, selective
    include_messages: bool = True
    include_context: bool = True
    custom_prompt: Optional[str] = None


class AIConversationSync(BaseModel):
    """Modelo para sincronizar conversas entre IAs."""

    ai_sessions: List[str]  # Lista de session_ids
    sync_strategy: str = "merge"  # merge, latest, selective
    conflict_resolution: str = "timestamp"  # timestamp, importance, manual


class SmartCacheQuery(BaseModel):
    """Consulta inteligente no cache multi-IA."""

    query: str
    ai_types: Optional[List[str]] = None
    time_range: Optional[int] = 30  # dias
    include_cross_ai: bool = True
    similarity_threshold: float = 0.7
    max_results: int = 10


# Cache de sessões ativas (em produção usar Redis)
_active_sessions: Dict[str, Dict[str, Any]] = {}
_ai_conversations: Dict[str, List[Dict[str, Any]]] = {}


def create_ai_session_endpoint(
    request: AISessionRequest, memory_service=Depends(get_memory)
):
    """Criar nova sessão de IA com cache inteligente."""
    try:
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Criar registro da sessão
        session_data = {
            "session_id": session_id,
            "ai_type": request.ai_type,
            "session_name": request.session_name,
            "user_id": request.user_id,
            "created_at": timestamp,
            "last_activity": timestamp,
            "context_summary": request.context_summary,
            "initial_prompt": request.initial_prompt,
            "message_count": 0,
            "importance_level": "normal",
            "metadata": request.metadata or {},
            "status": "active",
        }

        # Armazenar em cache ativo
        _active_sessions[session_id] = session_data

        # Armazenar no memory service
        memory_service.store_memory(
            content=f"""
=== NOVA SESSÃO {request.ai_type.upper()} ===

Sessão: {request.session_name}
ID: {session_id}
Usuário: {request.user_id}
Criada em: {timestamp}

Contexto inicial: {request.context_summary or 'Não especificado'}
Prompt inicial: {request.initial_prompt or 'Não especificado'}

Esta sessão será monitorada para cache inteligente entre IAs.
            """,
            memory_type="ai_session",
            tags=["ai_session", request.ai_type, "cache", request.user_id],
            metadata={
                "session_id": session_id,
                "ai_type": request.ai_type,
                "session_name": request.session_name,
                "user_id": request.user_id,
                "session_data": session_data,
            },
            importance_score=0.6,
        )

        return {
            "session_id": session_id,
            "status": "created",
            "ai_type": request.ai_type,
            "session_name": request.session_name,
            "cache_enabled": True,
            "endpoints": {
                "store_context": f"/ai/sessions/{session_id}/context",
                "retrieve_context": f"/ai/sessions/{session_id}/context",
                "cross_transfer": f"/ai/sessions/{session_id}/transfer",
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar sessão: {str(e)}")


def store_ai_context_endpoint(
    session_id: str, request: AIContextStore, memory_service=Depends(get_memory)
):
    """Armazenar contexto de conversa de IA com cache inteligente."""
    try:
        # Verificar se sessão existe
        if session_id not in _active_sessions:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")

        session = _active_sessions[session_id]
        timestamp = datetime.now().isoformat()

        # Atualizar dados da sessão
        session["last_activity"] = timestamp
        session["message_count"] += len(request.messages)

        # Calcular importância baseada no contexto
        context_length = len(request.context_summary)
        message_count = len(request.messages)
        calculated_importance = min(
            0.9,
            (context_length / 1000) * 0.3
            + (message_count / 10) * 0.3
            + request.importance_score * 0.4,
        )

        # Preparar conteúdo estruturado
        context_content = f"""
=== CONTEXTO {session['ai_type'].upper()} - {session['session_name']} ===

Sessão ID: {session_id}
Última atividade: {timestamp}
Total de mensagens: {session['message_count']}

RESUMO DO CONTEXTO:
{request.context_summary}

MENSAGENS RECENTES ({len(request.messages)}):
"""

        for i, msg in enumerate(request.messages[-5:], 1):  # Últimas 5 mensagens
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            content_preview = content[:200] + "..." if len(content) > 200 else content
            context_content += f"\n{i}. [{role.upper()}]: {content_preview}"

        context_content += f"""

ANÁLISE AUTOMÁTICA:
- Importância calculada: {calculated_importance:.2f}
- Tipo de IA: {session['ai_type']}
- Tags: {', '.join(request.tags or [])}
- Compatível para transferência cross-AI: Sim
"""

        # Armazenar no memory service
        memory_service.store_memory(
            content=context_content,
            memory_type="ai_context",
            tags=["ai_context", session["ai_type"], "conversation"]
            + (request.tags or []),
            metadata={
                "session_id": session_id,
                "ai_type": session["ai_type"],
                "message_count": len(request.messages),
                "context_summary": request.context_summary,
                "full_messages": request.messages,
                "importance_calculated": calculated_importance,
                "user_id": session.get("user_id"),
                "session_name": session["session_name"],
                "raw_metadata": request.metadata,
            },
            importance_score=calculated_importance,
        )

        # Atualizar cache de conversas
        if session_id not in _ai_conversations:
            _ai_conversations[session_id] = []

        _ai_conversations[session_id].append(
            {
                "timestamp": timestamp,
                "messages": request.messages,
                "context_summary": request.context_summary,
                "importance": calculated_importance,
            }
        )

        # Manter apenas últimas 10 interações no cache
        _ai_conversations[session_id] = _ai_conversations[session_id][-10:]

        return {
            "status": "stored",
            "session_id": session_id,
            "context_stored": True,
            "messages_count": len(request.messages),
            "calculated_importance": calculated_importance,
            "cache_position": len(_ai_conversations[session_id]),
            "cross_ai_compatible": True,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao armazenar contexto: {str(e)}"
        )


def retrieve_ai_context_endpoint(
    session_id: str,
    include_messages: bool = True,
    max_messages: int = 50,
    memory_service=Depends(get_memory),
):
    """Recuperar contexto de sessão de IA."""
    try:
        # Verificar cache ativo primeiro
        if session_id in _active_sessions:
            session = _active_sessions[session_id]

            # Buscar contextos no memory service
            contexts = memory_service.search_memory(
                query=f"session_id:{session_id}",
                memory_types=["ai_context"],
                max_results=10,
            )

            # Compilar contexto completo
            full_context = {
                "session_id": session_id,
                "ai_type": session["ai_type"],
                "session_name": session["session_name"],
                "created_at": session["created_at"],
                "last_activity": session["last_activity"],
                "total_messages": session["message_count"],
                "status": session["status"],
                "contexts_available": len(contexts),
            }

            if include_messages and contexts:
                all_messages = []
                for context in contexts:
                    metadata = context.get("metadata", {})
                    messages = metadata.get("full_messages", [])
                    all_messages.extend(messages)

                # Ordenar por timestamp e limitar
                all_messages = sorted(
                    all_messages, key=lambda x: x.get("timestamp", ""), reverse=True
                )[:max_messages]

                full_context["messages"] = all_messages
                full_context["context_summaries"] = [
                    {
                        "summary": ctx.get("metadata", {}).get("context_summary", ""),
                        "importance": ctx.get("metadata", {}).get(
                            "importance_calculated", 0
                        ),
                        "timestamp": ctx.get("timestamp", ""),
                    }
                    for ctx in contexts
                ]

            return full_context

        else:
            # Buscar no memory service
            sessions = memory_service.search_memory(
                query=f"session_id:{session_id}",
                memory_types=["ai_session", "ai_context"],
                max_results=20,
            )

            if not sessions:
                raise HTTPException(status_code=404, detail="Sessão não encontrada")

            # Reconstruir dados da sessão
            session_data = None
            contexts = []

            for item in sessions:
                if item.get("memory_type") == "ai_session":
                    session_data = item.get("metadata", {}).get("session_data", {})
                elif item.get("memory_type") == "ai_context":
                    contexts.append(item)

            if not session_data:
                raise HTTPException(
                    status_code=404, detail="Dados da sessão não encontrados"
                )

            return {
                "session_id": session_id,
                "session_data": session_data,
                "contexts": contexts[:5],  # Últimos 5 contextos
                "note": "Sessão recuperada do memory service (não estava em cache ativo)",
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao recuperar contexto: {str(e)}"
        )


def cross_ai_transfer_endpoint(
    request: CrossAITransfer, memory_service=Depends(get_memory)
):
    """Transferir contexto entre diferentes IAs."""
    try:
        # Recuperar contexto da sessão origem
        source_contexts = memory_service.search_memory(
            query=f"session_id:{request.source_session_id}",
            memory_types=["ai_context", "ai_session"],
            max_results=20,
        )

        if not source_contexts:
            raise HTTPException(status_code=404, detail="Sessão origem não encontrada")

        # Encontrar dados da sessão
        source_session = None
        context_data = []

        for item in source_contexts:
            if item.get("memory_type") == "ai_session":
                source_session = item.get("metadata", {}).get("session_data", {})
            elif item.get("memory_type") == "ai_context":
                context_data.append(item)

        if not source_session:
            raise HTTPException(
                status_code=404, detail="Dados da sessão origem não encontrados"
            )

        # Criar nova sessão para IA destino
        transfer_session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Compilar contexto para transferência
        if request.transfer_type == "full":
            # Transferência completa
            transfer_content = f"""
=== TRANSFERÊNCIA CROSS-AI: {source_session['ai_type'].upper()} → {request.target_ai_type.upper()} ===

SESSÃO ORIGEM:
- ID: {request.source_session_id}
- IA: {source_session['ai_type']}
- Nome: {source_session.get('session_name', 'Sem nome')}
- Criada: {source_session.get('created_at', 'Desconhecido')}
- Mensagens: {source_session.get('message_count', 0)}

CONTEXTO TRANSFERIDO:
"""

            # Incluir resumos de contexto
            for ctx in context_data[-3:]:  # Últimos 3 contextos
                metadata = ctx.get("metadata", {})
                summary = metadata.get("context_summary", "")
                transfer_content += f"\n--- Contexto ({ctx.get('timestamp', 'Sem data')}) ---\n{summary}\n"

            # Incluir mensagens se solicitado
            if request.include_messages:
                transfer_content += "\nMENSAGENS TRANSFERIDAS:\n"
                for ctx in context_data[-2:]:  # Últimas 2 sessões de mensagens
                    messages = ctx.get("metadata", {}).get("full_messages", [])
                    for msg in messages[-5:]:  # Últimas 5 mensagens de cada sessão
                        role = msg.get("role", "unknown")
                        content = (
                            msg.get("content", "")[:300] + "..."
                            if len(msg.get("content", "")) > 300
                            else msg.get("content", "")
                        )
                        transfer_content += f"\n[{role.upper()}]: {content}\n"

        elif request.transfer_type == "summary":
            # Apenas resumo
            summaries = [
                ctx.get("metadata", {}).get("context_summary", "")
                for ctx in context_data
                if ctx.get("metadata", {}).get("context_summary")
            ]

            transfer_content = f"""
=== RESUMO CROSS-AI: {source_session['ai_type'].upper()} → {request.target_ai_type.upper()} ===

Transferindo resumo da sessão "{source_session.get('session_name', 'Sem nome')}"

RESUMO CONSOLIDADO:
{' | '.join(summaries[-3:])}
"""

        # Adicionar prompt customizado se fornecido
        if request.custom_prompt:
            transfer_content += f"\n\nPROMPT CUSTOMIZADO PARA {request.target_ai_type.upper()}:\n{request.custom_prompt}"

        # Criar nova sessão para IA destino
        target_session_data = {
            "session_id": transfer_session_id,
            "ai_type": request.target_ai_type,
            "session_name": f"Transfer from {source_session['ai_type']} - {source_session.get('session_name', 'Unnamed')}",
            "user_id": source_session.get("user_id", "default"),
            "created_at": timestamp,
            "last_activity": timestamp,
            "context_summary": f"Transferido de {source_session['ai_type']} - {len(context_data)} contextos",
            "message_count": 0,
            "importance_level": "transfer",
            "metadata": {
                "transfer_source": request.source_session_id,
                "transfer_type": request.transfer_type,
                "original_ai": source_session["ai_type"],
            },
            "status": "active",
        }

        # Armazenar sessão transferida
        _active_sessions[transfer_session_id] = target_session_data

        memory_service.store_memory(
            content=transfer_content,
            memory_type="ai_transfer",
            tags=[
                "transfer",
                "cross_ai",
                source_session["ai_type"],
                request.target_ai_type,
            ],
            metadata={
                "transfer_session_id": transfer_session_id,
                "source_session_id": request.source_session_id,
                "source_ai": source_session["ai_type"],
                "target_ai": request.target_ai_type,
                "transfer_type": request.transfer_type,
                "session_data": target_session_data,
                "source_contexts_count": len(context_data),
            },
            importance_score=0.7,
        )

        return {
            "status": "transferred",
            "source_session_id": request.source_session_id,
            "target_session_id": transfer_session_id,
            "target_ai_type": request.target_ai_type,
            "transfer_type": request.transfer_type,
            "contexts_transferred": len(context_data),
            "messages_included": request.include_messages,
            "transfer_content_size": len(transfer_content),
            "ready_for_use": True,
            "endpoints": {
                "new_session_context": f"/ai/sessions/{transfer_session_id}/context",
                "retrieve_transfer": f"/ai/sessions/{transfer_session_id}/context",
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro na transferência cross-AI: {str(e)}"
        )


def smart_cache_search_endpoint(
    request: SmartCacheQuery, memory_service=Depends(get_memory)
):
    """Busca inteligente no cache multi-IA."""
    try:
        # Construir query de busca
        memory_types = ["ai_context", "ai_session", "ai_transfer"]

        # Filtrar por tipos de IA se especificado
        search_query = request.query
        if request.ai_types:
            ai_filter = " OR ".join([f"ai_type:{ai}" for ai in request.ai_types])
            search_query += f" AND ({ai_filter})"

        # Buscar memórias relevantes
        results = memory_service.search_memory(
            query=search_query,
            memory_types=memory_types,
            max_results=request.max_results * 2,  # Buscar mais para filtrar
            importance_threshold=0.3,
        )

        # Filtrar por data se especificado
        if request.time_range:
            cutoff_date = datetime.now() - timedelta(days=request.time_range)
            cutoff_str = cutoff_date.isoformat()

            filtered_results = []
            for result in results:
                result_date = result.get("timestamp", "")
                if result_date >= cutoff_str:
                    filtered_results.append(result)

            results = filtered_results

        # Classificar e formatar resultados
        formatted_results = []
        ai_types_found = set()

        for result in results[: request.max_results]:
            metadata = result.get("metadata", {})
            ai_type = metadata.get("ai_type", "unknown")
            ai_types_found.add(ai_type)

            formatted_result = {
                "relevance_score": result.get("relevance_score", 0),
                "ai_type": ai_type,
                "memory_type": result.get("memory_type"),
                "timestamp": result.get("timestamp"),
                "session_id": metadata.get("session_id"),
                "session_name": metadata.get("session_name", ""),
                "content_preview": result.get("content", "")[:300] + "..."
                if len(result.get("content", "")) > 300
                else result.get("content", ""),
                "importance": metadata.get(
                    "importance_calculated", result.get("importance", 0)
                ),
                "tags": result.get("tags", []),
                "cross_ai_compatible": result.get("memory_type")
                in ["ai_context", "ai_transfer"],
            }

            # Adicionar contexto específico para transferências
            if result.get("memory_type") == "ai_transfer":
                formatted_result["transfer_info"] = {
                    "source_ai": metadata.get("source_ai"),
                    "target_ai": metadata.get("target_ai"),
                    "transfer_type": metadata.get("transfer_type"),
                }

            formatted_results.append(formatted_result)

        # Estatísticas da busca
        search_stats = {
            "total_found": len(results),
            "returned": len(formatted_results),
            "ai_types_found": list(ai_types_found),
            "time_range_days": request.time_range,
            "cross_ai_results": len(
                [r for r in formatted_results if r.get("cross_ai_compatible")]
            ),
            "avg_relevance": sum(r.get("relevance_score", 0) for r in formatted_results)
            / len(formatted_results)
            if formatted_results
            else 0,
        }

        return {
            "query": request.query,
            "results": formatted_results,
            "search_stats": search_stats,
            "timestamp": datetime.now().isoformat(),
            "cache_recommendations": {
                "cross_ai_transfers_available": search_stats["cross_ai_results"] > 0,
                "best_ai_type": max(
                    ai_types_found,
                    key=lambda x: len(
                        [r for r in formatted_results if r.get("ai_type") == x]
                    ),
                )
                if ai_types_found
                else None,
                "relevance_quality": "high"
                if search_stats["avg_relevance"] > 0.7
                else "medium"
                if search_stats["avg_relevance"] > 0.5
                else "low",
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro na busca inteligente: {str(e)}"
        )


def get_ai_cache_stats_endpoint(memory_service=Depends(get_memory)):
    """Estatísticas do sistema de cache multi-IA."""
    try:
        # Buscar todas as memórias relacionadas a IA
        ai_memories = memory_service.search_memory(
            query="ai_type OR ai_session OR ai_context",
            memory_types=["ai_session", "ai_context", "ai_transfer"],
            max_results=1000,
        )

        # Análise estatística
        stats = {
            "total_memories": len(ai_memories),
            "active_sessions": len(_active_sessions),
            "cached_conversations": len(_ai_conversations),
            "by_ai_type": {},
            "by_memory_type": {},
            "recent_activity": {},
            "cross_ai_transfers": 0,
            "avg_importance": 0,
        }

        # Análise por tipo
        importance_scores = []
        recent_cutoff = datetime.now() - timedelta(days=7)

        for memory in ai_memories:
            # Tipo de IA
            metadata = memory.get("metadata", {})
            ai_type = metadata.get("ai_type", "unknown")
            stats["by_ai_type"][ai_type] = stats["by_ai_type"].get(ai_type, 0) + 1

            # Tipo de memória
            memory_type = memory.get("memory_type", "unknown")
            stats["by_memory_type"][memory_type] = (
                stats["by_memory_type"].get(memory_type, 0) + 1
            )

            # Transferências cross-AI
            if memory_type == "ai_transfer":
                stats["cross_ai_transfers"] += 1

            # Importância
            importance = metadata.get(
                "importance_calculated", memory.get("importance", 0)
            )
            importance_scores.append(importance)

            # Atividade recente
            timestamp_str = memory.get("timestamp", "")
            try:
                memory_date = datetime.fromisoformat(
                    timestamp_str.replace("Z", "+00:00")
                )
                if memory_date.replace(tzinfo=None) > recent_cutoff:
                    day_key = memory_date.strftime("%Y-%m-%d")
                    stats["recent_activity"][day_key] = (
                        stats["recent_activity"].get(day_key, 0) + 1
                    )
            except Exception:
                pass

        if importance_scores:
            stats["avg_importance"] = sum(importance_scores) / len(importance_scores)

        # Adicionar estatísticas de cache ativo
        stats["cache_details"] = {
            "session_types": {},
            "recent_sessions": 0,
            "conversation_sizes": [],
        }

        for session_id, session in _active_sessions.items():
            ai_type = session.get("ai_type", "unknown")
            stats["cache_details"]["session_types"][ai_type] = (
                stats["cache_details"]["session_types"].get(ai_type, 0) + 1
            )

            # Sessões recentes
            try:
                session_date = datetime.fromisoformat(session.get("last_activity", ""))
                if session_date > recent_cutoff:
                    stats["cache_details"]["recent_sessions"] += 1
            except Exception:
                pass

        # Tamanhos de conversas
        for session_id, conversations in _ai_conversations.items():
            stats["cache_details"]["conversation_sizes"].append(len(conversations))

        return {
            "cache_stats": stats,
            "system_health": {
                "cache_active": len(_active_sessions) > 0,
                "memory_service_active": True,
                "cross_ai_capability": stats["cross_ai_transfers"] > 0,
                "recent_activity_days": len(stats["recent_activity"]),
            },
            "recommendations": {
                "most_used_ai": max(stats["by_ai_type"].items(), key=lambda x: x[1])[0]
                if stats["by_ai_type"]
                else None,
                "cache_utilization": "high"
                if len(_active_sessions) > 5
                else "medium"
                if len(_active_sessions) > 0
                else "low",
                "transfer_utilization": "active"
                if stats["cross_ai_transfers"] > 0
                else "unused",
            },
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}"
        )


# Lista de todas as funções endpoint para integração
MULTI_AI_CACHE_ENDPOINTS = [
    ("POST", "/ai/sessions", create_ai_session_endpoint),
    ("POST", "/ai/sessions/{session_id}/context", store_ai_context_endpoint),
    ("GET", "/ai/sessions/{session_id}/context", retrieve_ai_context_endpoint),
    ("POST", "/ai/transfer", cross_ai_transfer_endpoint),
    ("POST", "/ai/cache/search", smart_cache_search_endpoint),
    ("GET", "/ai/cache/stats", get_ai_cache_stats_endpoint),
]

"""
INSTRUÇÕES DE INTEGRAÇÃO:

1. Importe este arquivo no ragpp_web_server.py:
   from multi_ai_cache_endpoints import MULTI_AI_CACHE_ENDPOINTS

2. Adicione os endpoints ao app FastAPI:
   for method, path, endpoint_func in MULTI_AI_CACHE_ENDPOINTS:
       if method == "POST":
           app.add_api_route(path, endpoint_func, methods=["POST"])
       elif method == "GET":
           app.add_api_route(path, endpoint_func, methods=["GET"])

3. Adicione get_memory import na área de imports:
   from ragpp.extended_memory_service import get_memory_service

FUNCIONALIDADES:
- Cache inteligente entre ChatGPT, Claude, Copilot, Gemini, etc.
- Transferência de contexto cross-AI
- Gerenciamento de sessões multiusuário
- Busca semântica no cache
- Estatísticas de uso
- Sincronização automática
"""
