#!/usr/bin/env python3
"""
Semantic LM Cache (optional)

Uses SentenceTransformer + ChromaDB to cache and retrieve near-duplicate prompts
with the same context fingerprint and model/provider constraints.

Env
- SEM_CACHE_THRESHOLD (default: 0.97)
- SEM_CACHE_PATH (default: ragpp/data/lm_semantic_cache)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import chromadb
    from chromadb.config import Settings
except Exception:
    chromadb = None  # type: ignore
    Settings = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None  # type: ignore


def _get_threshold() -> float:
    try:
        return float(os.getenv("SEM_CACHE_THRESHOLD", "0.97"))
    except Exception:
        return 0.97


def _base_path() -> Path:
    return Path(os.getenv("SEM_CACHE_PATH", "ragpp/data/lm_semantic_cache")).expanduser()


@dataclass
class SemHit:
    text: str
    score: float
    meta: Dict[str, Any]


class SemanticLMCache:
    def __init__(self):
        self.enabled = chromadb is not None and SentenceTransformer is not None
        if not self.enabled:
            self.client = None
            self.embedder = None
            self.col = None
            return
        self.client = chromadb.PersistentClient(
            path=str(_base_path()),
            settings=Settings(allow_reset=False, anonymized_telemetry=False),
        )
        self.col = self.client.get_or_create_collection(
            name="lm_sem_cache",
            metadata={"description": "Semantic cache for LLM responses"},
        )
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def is_available(self) -> bool:
        return self.enabled and self.col is not None and self.embedder is not None

    def _query_text(self, system_prompt: str, user_prompt: str) -> str:
        # Focus on user prompt; include system hash lightly
        return f"{system_prompt[:0]}{user_prompt}"  # keep API compatible, bias to user

    def find(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        context_fp: str,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> Optional[SemHit]:
        if not self.is_available():
            return None
        q = self._query_text(system_prompt, user_prompt)
        emb = self.embedder.encode([q])[0].tolist()
        res = self.col.query(
            query_embeddings=[emb],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )
        thr = _get_threshold()
        for i, _id in enumerate(res.get("ids", [[]])[0] or []):
            meta = res["metadatas"][0][i]
            doc = res["documents"][0][i]
            dist = res["distances"][0][i]
            score = 1.0 - float(dist)
            if score < thr:
                continue
            if (
                meta.get("provider") == provider
                and meta.get("model") == model
                and meta.get("context_fp") == context_fp
                and abs(float(meta.get("temperature", 0.7)) - float(temperature)) < 1e-3
            ):
                return SemHit(text=doc, score=score, meta=meta)
        return None

    def store(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        context_fp: str,
        response_text: str,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> None:
        if not self.is_available():
            return
        q = self._query_text(system_prompt, user_prompt)
        emb = self.embedder.encode([q])[0].tolist()
        meta = {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "context_fp": context_fp,
        }
        # Use incremental id
        _id = f"sem::{provider}::{model}::{hash(q + context_fp)}"
        self.col.upsert(ids=[_id], embeddings=[emb], metadatas=[meta], documents=[response_text])

