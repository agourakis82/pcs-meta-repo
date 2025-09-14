#!/usr/bin/env python3
"""
Importador de Conversas para MCP
Endpoint adicional para facilitar importação em lote
"""

import os
import tempfile
from typing import Any, Dict, List

# Importa o migrador que criamos
from chatgpt_conversation_migrator import ChatGPTMigrator
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

router = APIRouter(prefix="/import", tags=["import"])


class BulkImportRequest(BaseModel):
    """Request para importação em lote"""

    conversations: List[Dict[str, Any]]
    project_name: str = "Bulk Import"
    ai_type: str = "chatgpt"


class ImportStats(BaseModel):
    """Estatísticas de importação"""

    total_conversations: int
    successful_imports: int
    failed_imports: int
    session_ids: List[str]
    errors: List[str]


@router.post("/conversations/bulk", response_model=ImportStats)
async def bulk_import_conversations(request: BulkImportRequest):
    """
    Importa múltiplas conversas de uma vez

    Body exemplo:
    {
        "conversations": [
            {
                "title": "Discussão sobre IA",
                "messages": [
                    {"role": "user", "content": "O que é IA?", "timestamp": "2025-01-01T12:00:00Z"},
                    {"role": "assistant", "content": "IA é...", "timestamp": "2025-01-01T12:00:01Z"}
                ],
                "created_at": "2025-01-01T12:00:00Z"
            }
        ],
        "project_name": "Meu Projeto",
        "ai_type": "chatgpt"
    }
    """
    try:
        # Inicializa migrador
        migrator = ChatGPTMigrator()

        # Processa conversas usando o método do migrador
        results = migrator.migrate_to_mcp(request.conversations, request.project_name)

        return ImportStats(
            total_conversations=results["total_conversations"],
            successful_imports=results["successful_migrations"],
            failed_imports=results["failed_migrations"],
            session_ids=results["session_ids"],
            errors=results["errors"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na importação: {str(e)}")


@router.post("/conversations/file", response_model=ImportStats)
async def import_from_file(
    file: UploadFile = File(...),
    project_name: str = "File Import",
    ai_type: str = "chatgpt",
):
    """
    Importa conversas de um arquivo (JSON ou texto)

    Suporta:
    - Arquivo JSON do export oficial do ChatGPT
    - Arquivo de texto com conversas formatadas
    """
    try:
        # Lê conteúdo do arquivo
        content = await file.read()

        # Salva temporariamente
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".json" if file.filename.endswith(".json") else ".txt",
            encoding="utf-8",
        ) as temp_file:
            temp_file.write(content.decode("utf-8"))
            temp_path = temp_file.name

        try:
            # Processa arquivo usando o migrador
            migrator = ChatGPTMigrator()
            conversations = migrator.parse_chatgpt_export(temp_path)
            results = migrator.migrate_to_mcp(conversations, project_name)

            return ImportStats(
                total_conversations=results["total_conversations"],
                successful_imports=results["successful_migrations"],
                failed_imports=results["failed_migrations"],
                session_ids=results["session_ids"],
                errors=results["errors"],
            )

        finally:
            # Remove arquivo temporário
            os.unlink(temp_path)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar arquivo: {str(e)}"
        )


@router.get("/status")
async def import_status():
    """Status do sistema de importação"""
    try:
        # Testa conexão com MCP
        migrator = ChatGPTMigrator()
        mcp_available = migrator.validate_mcp_connection()

        return {
            "status": "online",
            "mcp_connection": "available" if mcp_available else "unavailable",
            "supported_formats": [
                "ChatGPT JSON Export",
                "Plain text conversations",
                "Bulk JSON import",
            ],
            "endpoints": [
                "/import/conversations/bulk",
                "/import/conversations/file",
                "/import/status",
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no status: {str(e)}")


# Template de exemplo para importação
EXAMPLE_IMPORT = {
    "conversations": [
        {
            "title": "Exemplo de Conversa",
            "created_at": "2025-01-01T12:00:00Z",
            "messages": [
                {
                    "role": "user",
                    "content": "Como implementar cache multi-IA?",
                    "timestamp": "2025-01-01T12:00:00Z",
                },
                {
                    "role": "assistant",
                    "content": "Para implementar um cache multi-IA você precisa...",
                    "timestamp": "2025-01-01T12:00:01Z",
                },
            ],
        }
    ],
    "project_name": "Projeto de Exemplo",
    "ai_type": "chatgpt",
}


@router.get("/example")
async def get_import_example():
    """Retorna exemplo de formato para importação"""
    return {
        "description": "Exemplo de formato para importação de conversas",
        "example": EXAMPLE_IMPORT,
        "usage": "POST /import/conversations/bulk com este formato no body",
    }
