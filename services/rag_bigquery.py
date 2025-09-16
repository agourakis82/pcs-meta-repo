"""
BigQuery-backed RAG engine with Vertex AI embeddings and generation.

This module provides a simple, self-contained knowledge base using
BigQuery as storage for document chunks and their vector embeddings.
It supports:
- Client initialization (BigQuery + Vertex AI)
- Dataset/table creation with a vector (FLOAT64 REPEATED) column
- Embedding generation via Vertex AI
- Document ingestion
- Semantic retrieval (cosine distance computed in SQL)
- Answer generation with retrieved context (Gemini)
- An optional ReAct-style iterative loop for multi-step queries

Environment/configuration is read from `services.settings` when available,
falling back to sensible defaults for local development.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

try:
    # Prefer project settings if available
    from services.settings import get_settings  # type: ignore
except Exception:  # pragma: no cover - optional import for standalone use
    get_settings = None  # type: ignore

logger = logging.getLogger(__name__)


# ------------------------------
# Data models
# ------------------------------


@dataclass
class KBConfig:
    project: str
    location: str
    dataset_id: str = "knowledge_base"
    table_id: str = "documents"
    embed_model: str = "textembedding-gecko@003"
    gen_model: str = "gemini-1.5-pro-002"


def _load_config() -> KBConfig:
    settings = get_settings() if callable(get_settings) else None
    project = (
        (settings.GCP_PROJECT if settings else None)
        or os.getenv("GCP_PROJECT")
        or os.getenv("PROJECT_ID")
        or "local-development"
    )
    location = (
        (getattr(settings, "LOCATION", None) if settings else None)
        or os.getenv("GCP_LOCATION")
        or os.getenv("LOCATION")
        or "us-central1"
    )
    embed_model = (
        (getattr(settings, "GEMINI_EMBED_MODEL", None) if settings else None)
        or os.getenv("GEMINI_EMBED_MODEL")
        or "textembedding-gecko@003"
    )
    gen_model = (
        (getattr(settings, "GEMINI_ANSWER_MODEL", None) if settings else None)
        or os.getenv("GEMINI_ANSWER_MODEL")
        or "gemini-1.5-pro-002"
    )
    return KBConfig(
        project=project,
        location=location,
        embed_model=embed_model,
        gen_model=gen_model,
    )


class BigQueryRAG:
    """BigQuery-backed RAG engine."""

    def __init__(
        self,
        dataset_id: str = "knowledge_base",
        table_id: str = "documents",
        project: Optional[str] = None,
        location: Optional[str] = None,
        embed_model: Optional[str] = None,
        gen_model: Optional[str] = None,
    ) -> None:
        cfg = _load_config()
        self.project = project or cfg.project
        self.location = location or cfg.location
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.embed_model = embed_model or cfg.embed_model
        self.gen_model = gen_model or cfg.gen_model

        self._bq = None
        self._embedder = None
        self._generator = None

    # ------------------------------
    # Clients
    # ------------------------------
    def _ensure_clients(self) -> None:
        if self._bq is None:
            from google.cloud import bigquery

            self._bq = bigquery.Client(project=self.project)

        if self._embedder is None or self._generator is None:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            from vertexai.language_models import TextEmbeddingModel

            vertexai.init(project=self.project, location=self.location)
            self._embedder = TextEmbeddingModel.from_pretrained(self.embed_model)
            self._generator = GenerativeModel(self.gen_model)

    # ------------------------------
    # Schema management
    # ------------------------------
    def ensure_schema(self) -> str:
        """Create dataset and table if they do not exist. Returns full table id."""
        self._ensure_clients()
        from google.cloud import bigquery

        dataset_ref = bigquery.Dataset(f"{self.project}.{self.dataset_id}")
        try:
            self._bq.create_dataset(dataset_ref, exists_ok=True)
        except TypeError:
            # For older client versions without exists_ok
            try:
                self._bq.get_dataset(dataset_ref)
            except Exception:
                self._bq.create_dataset(dataset_ref)

        table_ref = f"{self.project}.{self.dataset_id}.{self.table_id}"
        schema = [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
            bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="NULLABLE"),
        ]
        table = bigquery.Table(table_ref, schema=schema)
        try:
            self._bq.create_table(table, exists_ok=True)
        except TypeError:
            try:
                self._bq.get_table(table)
            except Exception:
                self._bq.create_table(table)

        logger.info("Using BigQuery table %s for knowledge storage", table_ref)
        return table_ref

    # ------------------------------
    # Embeddings
    # ------------------------------
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text using Vertex AI."""
        self._ensure_clients()
        # Some SDK versions are sync-only for embeddings
        resp = self._embedder.get_embeddings([text])
        return list(resp[0].values)

    # ------------------------------
    # Ingestion
    # ------------------------------
    def add_document(self, doc_id: str, content: str, source: str = "") -> None:
        """Embed content and insert into BigQuery."""
        self._ensure_clients()
        from google.cloud import bigquery

        table_ref = f"{self.project}.{self.dataset_id}.{self.table_id}"
        vector = self.get_embedding(content)
        row = {
            "id": doc_id,
            "content": content,
            "embedding": vector,
            "source": source,
            "created_at": bigquery.ScalarQueryParameter(
                "created_at", "TIMESTAMP", time.strftime("%Y-%m-%d %H:%M:%S")
            ).value,
        }
        errors = self._bq.insert_rows_json(table_ref, [row])
        if errors:
            logger.error("Failed to insert rows: %s", errors)
            raise RuntimeError(f"BigQuery insert failed: {errors}")
        logger.info("Inserted document %s into knowledge base", doc_id)

    # ------------------------------
    # Retrieval
    # ------------------------------
    def _cosine_search_sql(self) -> str:
        """SQL to compute cosine distance using array math; portable across BQ versions."""
        full_table = f"`{self.project}.{self.dataset_id}.{self.table_id}`"
        # Compute dot, norms with UNNEST+OFFSET to align vector elements
        return f"""
WITH q AS (
  SELECT @qvec AS qvec,
         (SELECT SQRT(SUM(qq * qq)) FROM UNNEST(@qvec) AS qq) AS norm_q
),
per_elem AS (
  SELECT
    d.id,
    d.content,
    d.source,
    e AS e_val,
    off AS e_off
  FROM {full_table} AS d,
  UNNEST(d.embedding) AS e WITH OFFSET AS off
),
acc AS (
  SELECT
    p.id,
    ANY_VALUE(p.content) AS content,
    ANY_VALUE(p.source) AS source,
    SUM(p.e_val * q.qvec[OFFSET(p.e_off)]) AS dot,
    SQRT(SUM(p.e_val * p.e_val)) AS norm_d,
    ANY_VALUE(q.norm_q) AS norm_q
  FROM per_elem AS p
  CROSS JOIN q
  GROUP BY p.id
)
SELECT content, source,
       1 - (dot / NULLIF(norm_d * norm_q, 0)) AS cosine_distance
FROM acc
ORDER BY cosine_distance ASC
LIMIT @top_k
"""

    def query(self, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Return top_k most relevant documents for the question."""
        self._ensure_clients()
        from google.cloud import bigquery

        q_vector = self.get_embedding(question)
        sql = self._cosine_search_sql()
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("qvec", "FLOAT64", q_vector),
                bigquery.ScalarQueryParameter("top_k", "INT64", int(top_k)),
            ]
        )
        job = self._bq.query(sql, job_config=job_config)
        rows = list(job.result())
        results: List[Dict[str, Any]] = []
        for r in rows:
            results.append(
                {
                    "content": r["content"],
                    "source": r.get("source"),
                    "cosine_distance": float(r["cosine_distance"])
                    if r["cosine_distance"] is not None
                    else 1.0,
                }
            )
        return results

    # ------------------------------
    # Generation
    # ------------------------------
    def answer(self, question: str, top_k: int = 5) -> str:
        """Generate an answer using retrieved documents as context."""
        self._ensure_clients()
        docs = self.query(question, top_k=top_k)
        context_parts: List[str] = []
        for d in docs:
            src = d.get("source") or ""
            ctx = d.get("content") or ""
            if ctx:
                context_parts.append(f"Source: {src}\nContent: {ctx}")
        context = "\n\n".join(context_parts)
        prompt = (
            f"QUESTION: {question}\n"
            f"Using the following sources, answer the question with a concise explanation and cite the sources.\n"
            f"{context}\nANSWER:"
        )
        resp = self._generator.generate_content(prompt)
        return (resp.text or "").strip()

    # ------------------------------
    # ReAct loop (iterative)
    # ------------------------------
    def answer_iterative(self, question: str, max_steps: int = 10) -> str:
        """Simple ReAct-style loop over BigQuery KB."""
        self._ensure_clients()
        accumulated = []
        for step in range(max_steps):
            history = "\n".join(accumulated)
            prompt = (
                "You are a research assistant with access to a knowledge base.\n"
                "Your task is to answer the question using the knowledge base. "
                "You can SEARCH the knowledge base for more info or give a FINAL answer.\n"
                "Format: Thought: <your thinking>\nAction: <SEARCH or FINAL>[<query or answer>]\n"
                f"Question: {question}\n"
                f"{history}\n"
                "Thought: "
            )
            resp = self._generator.generate_content(prompt)
            reaction = (resp.text or "").strip()
            if reaction.upper().startswith("FINAL:"):
                return reaction[len("FINAL:") :].strip()
            if reaction.upper().startswith("SEARCH:"):
                search_query = reaction[len("SEARCH:") :].strip()
                results = self.query(search_query, top_k=3)
                obs_lines = []
                for res in results:
                    obs_lines.append(f"[Result] {res.get('content','')}")
                accumulated.append(
                    f"Thought: {search_query}\nAction: SEARCH\nObservation:\n" + "\n".join(obs_lines)
                )
                continue
            # Fallback if unrecognized
            return reaction
        return "No conclusive answer."


# Convenience functions (compatible with the prompt sequence in the plan)

_singleton: Optional[BigQueryRAG] = None


def _get_singleton() -> BigQueryRAG:
    global _singleton
    if _singleton is None:
        _singleton = BigQueryRAG()
        _singleton.ensure_schema()
    return _singleton


def get_embedding(text: str) -> List[float]:
    return _get_singleton().get_embedding(text)


def add_document(doc_id: str, content: str, source: str = "") -> None:
    return _get_singleton().add_document(doc_id, content, source)


def query_knowledge_base(question: str, top_k: int = 5) -> List[Dict[str, Any]]:
    return _get_singleton().query(question, top_k)


def answer_question(question: str) -> str:
    return _get_singleton().answer(question)


def answer_question_iterative(question: str) -> str:
    return _get_singleton().answer_iterative(question)

