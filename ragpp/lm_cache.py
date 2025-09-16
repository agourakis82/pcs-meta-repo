#!/usr/bin/env python3
"""
LM Cache for RAG++

Lightweight SQLite-based cache for LLM completions, with helper functions to
compute deterministic keys and context fingerprints.

Env vars
- ENABLE_LM_CACHE (default: "1")
- NO_LM_CACHE     (default: "0")
- LM_CACHE_TTL_SECONDS (default: 86400)
- LM_CACHE_PATH   (default: ragpp/data/lm_cache.db)
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


def _now() -> float:
    return time.time()


def _default_db_path() -> Path:
    return Path(os.getenv("LM_CACHE_PATH", "ragpp/data/lm_cache.db")).expanduser()


def _ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class CacheHit:
    key: str
    value: str
    expires_at: float
    created_at: float
    hits: int


class LMLocalCache:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or _default_db_path()
        _ensure_parent(self.db_path)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL,
              expires_at REAL NOT NULL,
              created_at REAL NOT NULL,
              hits INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_expires_at ON entries(expires_at)"
        )
        self._conn.commit()

    def get(self, key: str) -> Optional[str]:
        if not self._enabled():
            return None
        now = _now()
        with self._lock:
            cur = self._conn.execute(
                "SELECT value, expires_at, created_at, hits FROM entries WHERE key=?",
                (key,),
            )
            row = cur.fetchone()
            if not row:
                return None
            value, expires_at, created_at, hits = row
            if expires_at < now:
                # Expired: remove
                self._conn.execute("DELETE FROM entries WHERE key=?", (key,))
                self._conn.commit()
                return None
            # Update hits
            self._conn.execute(
                "UPDATE entries SET hits = ? WHERE key = ?", (int(hits) + 1, key)
            )
            self._conn.commit()
            return value

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None):
        if not self._enabled():
            return
        ttl = int(os.getenv("LM_CACHE_TTL_SECONDS", "86400"))
        if ttl_seconds is not None:
            ttl = int(ttl_seconds)
        now = _now()
        exp = now + max(1, ttl)
        with self._lock:
            self._conn.execute(
                "REPLACE INTO entries (key, value, expires_at, created_at, hits) VALUES (?,?,?,?,?)",
                (key, value, exp, now, 0),
            )
            self._conn.commit()

    def cleanup(self):
        now = _now()
        with self._lock:
            self._conn.execute("DELETE FROM entries WHERE expires_at < ?", (now,))
            self._conn.commit()

    def _enabled(self) -> bool:
        if os.getenv("NO_LM_CACHE", "0").strip() in ("1", "true", "yes"):
            return False
        return os.getenv("ENABLE_LM_CACHE", "1").strip() not in ("0", "false", "no")


_global_cache: Optional[LMLocalCache] = None


def get_lm_cache() -> LMLocalCache:
    global _global_cache
    if _global_cache is None:
        _global_cache = LMLocalCache()
    return _global_cache


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def make_key(
    provider: str,
    model: str,
    temperature: float,
    top_p: float,
    system_prompt: str,
    user_prompt: str,
    context_fingerprint: str = "",
) -> str:
    payload = {
        "provider": provider,
        "model": model,
        "temperature": round(float(temperature), 3),
        "top_p": round(float(top_p), 3),
        "system_hash": _sha256(system_prompt or ""),
        "user_hash": _sha256(user_prompt or ""),
        "context_fp": context_fingerprint or "",
    }
    return _sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def fingerprint_context(rag_context: Dict[str, Any]) -> str:
    """
    Build a stable fingerprint from rag_context structures.
    Supports keys like 'rag_results', 'literature_results', 'mcp_results'.
    """
    if not rag_context:
        return ""
    ids: list[str] = []
    try:
        # Literature/RAG
        for key in ("rag_results", "literature_results"):
            for item in rag_context.get(key, []) or []:
                meta = item.get("metadata", {}) if isinstance(item, dict) else {}
                rec = (
                    item.get("record_id")
                    or meta.get("record_id")
                    or meta.get("pmid")
                    or meta.get("id")
                )
                if rec:
                    ids.append(str(rec))
        # Memory
        for item in rag_context.get("mcp_results", []) or []:
            mid = item.get("memory_id") or item.get("id")
            if mid:
                ids.append(str(mid))
    except Exception:
        pass
    if not ids:
        # Fallback: hash subset of context
        try:
            return _sha256(json.dumps(rag_context, sort_keys=True)[:4096])
        except Exception:
            return ""
    ids = sorted(set(ids))
    return _sha256("|".join(ids))

