"""
Darwin Platform Memory Router

Project memory and session logging functionality.
Provides JSONL-based session storage with search capabilities.
"""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.security import rate_limit, require_api_key
from services.rag_vertex import get_rag

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/memory",
    tags=["Memory"],
    dependencies=[Depends(require_api_key), Depends(rate_limit)],
)


class SessionLogEntry(BaseModel):
    """Session log entry model."""

    summary: str = Field(..., description="Session summary")
    tags: List[str] = Field(default_factory=list, description="Session tags")
    actor: Optional[str] = Field(None, description="Session actor/user")


class SessionLogResponse(BaseModel):
    """Session log response model."""

    request_id: str = Field(..., description="Unique request ID")
    timestamp_utc: datetime = Field(..., description="UTC timestamp")
    summary: str = Field(..., description="Session summary")
    tags: List[str] = Field(..., description="Session tags")
    actor: Optional[str] = Field(None, description="Session actor/user")


class MemorySearchResponse(BaseModel):
    """Memory search response model."""

    query: str = Field(..., description="Search query")
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total results found")


class MemoryStorage:
    """Memory storage manager."""

    def __init__(self, storage_path: str = "data/memory"):
        """
        Initialize memory storage.

        Args:
            storage_path: Base path for storage files
        """
        self.storage_path = storage_path
        self.jsonl_file = os.path.join(storage_path, "sessions.jsonl")
        self.db_file = os.path.join(storage_path, "sessions.db")

        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for sessions."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT UNIQUE NOT NULL,
                    timestamp_utc TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    actor TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for search performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_timestamp 
                ON sessions(timestamp_utc)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_summary 
                ON sessions(summary)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_tags 
                ON sessions(tags)
            """)

    async def log_session(self, entry: SessionLogEntry) -> SessionLogResponse:
        """
        Log a session entry.

        Args:
            entry: Session log entry

        Returns:
            Session log response with metadata
        """
        request_id = str(uuid.uuid4())
        timestamp_utc = datetime.now(timezone.utc)

        # Create response object
        response = SessionLogResponse(
            request_id=request_id,
            timestamp_utc=timestamp_utc,
            summary=entry.summary,
            tags=entry.tags,
            actor=entry.actor,
        )

        # Store in JSONL file
        jsonl_entry = {
            "request_id": request_id,
            "timestamp_utc": timestamp_utc.isoformat(),
            "summary": entry.summary,
            "tags": entry.tags,
            "actor": entry.actor,
        }

        try:
            with open(self.jsonl_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(jsonl_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to JSONL file: {e}")

        # Store in SQLite database
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute(
                    """
                    INSERT INTO sessions 
                    (request_id, timestamp_utc, summary, tags, actor)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        request_id,
                        timestamp_utc.isoformat(),
                        entry.summary,
                        json.dumps(entry.tags),
                        entry.actor,
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to write to SQLite database: {e}")
            # Don't fail the request if DB write fails

        logger.info(f"Logged session: {request_id}")
        return response

    async def search_sessions(
        self, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search session logs.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of matching sessions
        """
        results = []

        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.row_factory = sqlite3.Row

                # Simple text search in summary and tags
                cursor = conn.execute(
                    """
                    SELECT request_id, timestamp_utc, summary, tags, actor
                    FROM sessions
                    WHERE summary LIKE ? OR tags LIKE ?
                    ORDER BY timestamp_utc DESC
                    LIMIT ?
                """,
                    (f"%{query}%", f"%{query}%", limit),
                )

                for row in cursor:
                    results.append(
                        {
                            "request_id": row["request_id"],
                            "timestamp_utc": row["timestamp_utc"],
                            "summary": row["summary"],
                            "tags": json.loads(row["tags"]) if row["tags"] else [],
                            "actor": row["actor"],
                        }
                    )

        except Exception as e:
            logger.error(f"Failed to search sessions: {e}")
            # Fall back to JSONL search if DB fails
            results = await self._search_jsonl(query, limit)

        return results

    async def _search_jsonl(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback search using JSONL file."""
        results = []

        if not os.path.exists(self.jsonl_file):
            return results

        try:
            with open(self.jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    if len(results) >= limit:
                        break

                    try:
                        entry = json.loads(line.strip())
                        if query.lower() in entry.get("summary", "").lower() or any(
                            query.lower() in tag.lower()
                            for tag in entry.get("tags", [])
                        ):
                            results.append(entry)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Failed to search JSONL file: {e}")

        return results


# Global memory storage instance
memory_storage = MemoryStorage()


@router.post("/session/log", response_model=SessionLogResponse)
async def log_session(entry: SessionLogEntry) -> SessionLogResponse:
    """
    Log a session entry with timestamp and request ID.

    Args:
        entry: Session log entry

    Returns:
        Session log response with metadata
    """
    return await memory_storage.log_session(entry)


@router.get("/search", response_model=MemorySearchResponse)
async def search_memory(
    q: str = Query(..., description="Search query"),
    k: int = Query(5, ge=1, le=50, description="Number of results"),
) -> MemorySearchResponse:
    """
    Search project memory using RAG.

    Args:
        q: Search query
        k: Number of results to return

    Returns:
        Search results with citations
    """
    try:
        # Use RAG to search for relevant information
        rag_backend = get_rag()
        rag_response = await rag_backend.retrieve(q, k)

        # Also search local session logs
        session_results = await memory_storage.search_sessions(q, k)

        # Combine results
        all_results = []

        # Add RAG sources
        for source in rag_response.sources:
            all_results.append(
                {
                    "type": "rag_source",
                    "title": source.title,
                    "snippet": source.snippet,
                    "url_or_doi": source.url_or_doi,
                    "score": source.score,
                    "backend": rag_response.backend_type,
                }
            )

        # Add session logs
        for session in session_results:
            all_results.append(
                {
                    "type": "session_log",
                    "request_id": session["request_id"],
                    "timestamp": session["timestamp_utc"],
                    "summary": session["summary"],
                    "tags": session["tags"],
                    "actor": session.get("actor"),
                }
            )

        return MemorySearchResponse(
            query=q, results=all_results, total_found=len(all_results)
        )

    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        raise HTTPException(status_code=500, detail="Memory search failed")


def get_memory_storage() -> MemoryStorage:
    """Get memory storage instance."""
    return memory_storage
