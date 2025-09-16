"""Darwin Platform RAG++ Enhanced Research Agent Service

Native integration of the RAG++ system into Darwin platform architecture.
Provides long-horizon reasoning, scientific discovery, and iterative search.

Based on RAG++ Enhanced Research Agent implementation.
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class RAGPlusConfig:
    """Configuration for RAG++ system within Darwin"""

    project_id: str
    location: str = "us-central1"
    dataset_id: str = "darwin_knowledge_base"
    table_id: str = "documents"
    embedding_model: str = "textembedding-gecko@001"
    generation_model: str = "text-bison@001"
    novelty_threshold: float = 0.8
    max_iterations: int = 10
    top_k_retrieval: int = 5
    discovery_enabled: bool = True
    discovery_interval: int = 3600  # seconds


@dataclass
class SourceConfig:
    """Scientific source configuration"""

    name: str
    type: str
    url: str
    enabled: bool = True
    check_interval: int = 3600


class DarwinRAGPlusService:
    """
    Darwin Platform native RAG++ service.

    Integrates seamlessly with Darwin's architecture while providing
    advanced long-horizon reasoning and scientific discovery capabilities.
    """

    def __init__(self, config: Optional[RAGPlusConfig] = None):
        settings = get_settings()

        # Prefer explicit RAG++ project if set; fallback to platform project
        project_id = getattr(settings, "RAG_PLUS_PROJECT_ID", None) or settings.PROJECT_ID

        self.config = config or RAGPlusConfig(
            project_id=project_id,
            location=settings.LOCATION,
            dataset_id=getattr(
                settings, "RAG_PLUS_DATASET_ID", "darwin_knowledge_base"
            ),
            table_id=getattr(settings, "RAG_PLUS_TABLE_ID", "documents"),
            embedding_model=getattr(
                settings, "RAG_PLUS_EMBEDDING_MODEL", "textembedding-gecko@001"
            ),
            generation_model=getattr(
                settings, "RAG_PLUS_GENERATION_MODEL", "text-bison@001"
            ),
            novelty_threshold=getattr(settings, "RAG_PLUS_NOVELTY_THRESHOLD", 0.8),
            max_iterations=getattr(settings, "RAG_PLUS_MAX_ITERATIONS", 10),
            top_k_retrieval=getattr(settings, "RAG_PLUS_TOP_K_RETRIEVAL", 5),
            discovery_enabled=getattr(settings, "RAG_PLUS_DISCOVERY_ENABLED", True),
            discovery_interval=getattr(settings, "RAG_PLUS_DISCOVERY_INTERVAL", 3600),
        )

        self.seen_articles: set[str] = set()
        self._monitoring_task: Optional[asyncio.Task] = None

        # Initialize clients
        self._init_clients()
        self._setup_knowledge_base()

        # Scientific sources
        self.sources = self._get_scientific_sources()

        logger.info(
            f"Darwin RAG++ Service initialized for project {self.config.project_id}"
        )

    def _init_clients(self):
        """Initialize Vertex AI and BigQuery clients"""
        try:
            # Initialize Vertex AI
            import vertexai
            from vertexai.language_models import (
                TextEmbeddingModel,
                TextGenerationModel,
            )
            from google.cloud import bigquery

            vertexai.init(
                project=self.config.project_id, location=self.config.location
            )

            # Initialize BigQuery client
            self.bq_client = bigquery.Client(project=self.config.project_id)

            # Initialize models
            self.embedding_model = TextEmbeddingModel.from_pretrained(
                self.config.embedding_model
            )
            self.generation_model = TextGenerationModel.from_pretrained(
                self.config.generation_model
            )

            logger.info("RAG++ clients initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG++ clients: {e}")
            raise

    def _setup_knowledge_base(self):
        """Setup BigQuery knowledge base schema"""
        try:
            from google.cloud import bigquery
            from google.cloud.exceptions import NotFound

            # Create dataset if not exists
            dataset_ref = self.bq_client.dataset(self.config.dataset_id)
            try:
                self.bq_client.get_dataset(dataset_ref)
                logger.info(f"Using existing dataset {self.config.dataset_id}")
            except NotFound:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = self.config.location
                self.bq_client.create_dataset(dataset)
                logger.info(f"Created dataset {self.config.dataset_id}")

            # Define table schema for RAG++ knowledge base
            schema = [
                bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
                bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="NULLABLE"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("discovery_type", "STRING", mode="NULLABLE"),
            ]

            # Create table if not exists
            table_ref = (
                f"{self.config.project_id}."
                f"{self.config.dataset_id}."
                f"{self.config.table_id}"
            )
            try:
                self.bq_client.get_table(table_ref)
                logger.info(f"Using existing table {table_ref}")
            except NotFound:
                table = bigquery.Table(table_ref, schema=schema)
                self.bq_client.create_table(table)
                logger.info(f"Created table {table_ref}")

        except Exception as e:
            logger.error(f"Error setting up knowledge base: {e}")
            raise

    def _get_scientific_sources(self) -> List[SourceConfig]:
        """Get configured scientific sources"""
        return [
            SourceConfig(
                name="arXiv_CS_AI",
                type="rss",
                url="http://export.arxiv.org/rss/cs.AI",
                check_interval=3600,
            ),
            SourceConfig(
                name="arXiv_CS_LG",
                type="rss",
                url="http://export.arxiv.org/rss/cs.LG",
                check_interval=3600,
            ),
            SourceConfig(
                name="Nature_AI",
                type="rss",
                url="https://www.nature.com/subjects/machine-learning.rss",
                check_interval=7200,
            ),
            SourceConfig(
                name="ScienceDaily_AI",
                type="rss",
                url="https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
                check_interval=7200,
            ),
        ]

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            text = text.strip()[:10000]  # Token limit
            response = self.embedding_model.get_embeddings([text])
            vector = response[0].values
            return list(vector)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    async def add_document(
        self,
        doc_id: str,
        content: str,
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        discovery_type: str = "manual",
    ) -> bool:
        """Add document to knowledge base"""
        try:
            vector = await self.get_embedding(content)
            if not vector:
                return False

            row = {
                "id": doc_id,
                "content": content,
                "embedding": vector,
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
                "discovery_type": discovery_type,
            }

            table_ref = (
                f"{self.config.project_id}."
                f"{self.config.dataset_id}."
                f"{self.config.table_id}"
            )
            errors = self.bq_client.insert_rows_json(table_ref, [row])

            if errors:
                logger.error(f"Failed to insert document {doc_id}: {errors}")
                return False
            else:
                logger.info(f"Added document to Darwin knowledge base: {doc_id}")
                return True

        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            return False

    async def query_knowledge_base(
        self, question: str, top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Query knowledge base with semantic search"""
        try:
            top_k = top_k or self.config.top_k_retrieval
            q_vector = await self.get_embedding(question)
            if not q_vector:
                return []

            vector_str = ", ".join(map(str, q_vector))

            query = f"""
            SELECT 
                content, 
                source,
                discovery_type,
                timestamp,
                metadata,
                (1 - (
                    DOT_PRODUCT(embedding, [{vector_str}]) / 
                    (SQRT(DOT_PRODUCT(embedding, embedding)) * 
                     SQRT(DOT_PRODUCT([{vector_str}], [{vector_str}])))
                )) AS cosine_distance
            FROM `{self.config.project_id}.{self.config.dataset_id}.{self.config.table_id}`
            ORDER BY cosine_distance ASC
            LIMIT {top_k}
            """

            query_job = self.bq_client.query(query)
            results = []

            for row in query_job.result():
                results.append(
                    {
                        "content": row.content,
                        "source": row.source,
                        "discovery_type": row.discovery_type,
                        "timestamp": row.timestamp.isoformat()
                        if row.timestamp
                        else None,
                        "metadata": row.metadata,
                        "cosine_distance": float(row.cosine_distance),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return []

    async def answer_question(self, question: str) -> Dict[str, Any]:
        """Generate answer using RAG"""
        try:
            docs = await self.query_knowledge_base(question)

            if not docs:
                return {
                    "answer": "Desculpe, não encontrei informações relevantes na base de conhecimento.",
                    "sources": [],
                    "method": "simple_rag",
                }

            # Build context
            context = ""
            sources = []
            for i, doc in enumerate(docs, 1):
                content = doc.get("content", "")
                source = doc.get("source", "")
                if content:
                    context += f"[{i}] Fonte: {source}\nConteúdo: {content}\n\n"
                    sources.append(
                        {
                            "index": i,
                            "source": source,
                            "discovery_type": doc.get("discovery_type"),
                            "timestamp": doc.get("timestamp"),
                            "relevance_score": 1 - doc.get("cosine_distance", 1),
                        }
                    )

            # Generate answer
            prompt = (
                f"PERGUNTA: {question}\n\n"
                f"Com base nas seguintes fontes científicas, responda de forma "
                f"precisa e cite as fontes numeradas:\n\n{context}\n"
                f"RESPOSTA:"
            )

            params = {"temperature": 0.2, "max_output_tokens": 512}
            response = self.generation_model.predict(prompt, **params)
            answer = response.text.strip()

            return {
                "answer": answer,
                "sources": sources,
                "method": "simple_rag",
                "retrieved_docs": len(docs),
            }

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                "answer": f"Erro ao gerar resposta: {e}",
                "sources": [],
                "method": "error",
            }

    async def answer_question_iterative(self, question: str) -> Dict[str, Any]:
        """Generate answer using ReAct iterative reasoning"""
        try:
            accumulated_info = ""
            reasoning_steps = []

            for step in range(self.config.max_iterations):
                prompt = (
                    "Você é um assistente de pesquisa científica com acesso à base de conhecimento Darwin.\n"
                    "Responda usando informações precisas. Você pode BUSCAR mais informações ou dar resposta FINAL.\n\n"
                    "Formato:\n"
                    "Pensamento: <raciocínio>\n"
                    "Ação: BUSCAR[<consulta>] ou FINAL[<resposta>]\n\n"
                    f"Pergunta: {question}\n"
                    f"{accumulated_info}\n"
                    "Pensamento: "
                )

                params = {"temperature": 0.3, "max_output_tokens": 256}
                response = self.generation_model.predict(prompt, **params)
                reaction = response.text.strip()

                reasoning_steps.append({"step": step + 1, "reaction": reaction})

                if "FINAL[" in reaction:
                    start = reaction.find("FINAL[") + 6
                    end = reaction.find("]", start)
                    if end != -1:
                        answer = reaction[start:end].strip()
                        return {
                            "answer": answer,
                            "method": "iterative_react",
                            "reasoning_steps": reasoning_steps,
                            "total_steps": step + 1,
                        }
                    else:
                        return {
                            "answer": reaction,
                            "method": "iterative_react",
                            "reasoning_steps": reasoning_steps,
                            "total_steps": step + 1,
                        }

                elif "BUSCAR[" in reaction:
                    start = reaction.find("BUSCAR[") + 7
                    end = reaction.find("]", start)
                    if end != -1:
                        search_query = reaction[start:end].strip()

                        # Perform search
                        results = await self.query_knowledge_base(search_query, top_k=3)

                        # Format observations
                        obs_text = ""
                        for res in results:
                            content_preview = res.get("content", "")[:200] + "..."
                            obs_text += f"[Resultado] {content_preview}\n"

                        accumulated_info += f"{reaction}\nObservação:\n{obs_text}\n"
                        continue
                else:
                    return {
                        "answer": reaction,
                        "method": "iterative_react",
                        "reasoning_steps": reasoning_steps,
                        "total_steps": step + 1,
                    }

            return {
                "answer": "Não foi possível chegar a uma resposta conclusiva após máximo de iterações.",
                "method": "iterative_react",
                "reasoning_steps": reasoning_steps,
                "total_steps": self.config.max_iterations,
            }

        except Exception as e:
            logger.error(f"Error in iterative reasoning: {e}")
            return {
                "answer": f"Erro no raciocínio iterativo: {e}",
                "method": "error",
                "reasoning_steps": [],
            }

    async def discover_new_knowledge(self) -> Dict[str, int]:
        """Scientific discovery from RSS feeds"""
        if not self.config.discovery_enabled:
            return {"status": "disabled"}

        stats = {"fetched": 0, "novel": 0, "added": 0, "errors": 0}

        try:
            # Lazy import to avoid hard dependency at app import time
            import feedparser  # type: ignore
            # Fetch articles from sources
            new_articles = []
            for source in self.sources:
                if not source.enabled:
                    continue

                try:
                    feed = feedparser.parse(source.url)
                    for entry in feed.entries:
                        entry_id = entry.get("id") or entry.get("link") or ""
                        if not entry_id:
                            continue

                        article_hash = hashlib.md5(entry_id.encode()).hexdigest()

                        if article_hash not in self.seen_articles:
                            self.seen_articles.add(article_hash)

                            title = entry.get("title", "")
                            link = entry.get("link", "")
                            content = (
                                entry.get("summary") or entry.get("description") or ""
                            )

                            if title and content:
                                new_articles.append((title, content, link, source.name))

                except Exception as e:
                    logger.error(f"Error fetching from {source.name}: {e}")
                    stats["errors"] += 1

            stats["fetched"] = len(new_articles)

            # Process novel articles
            for title, content, url, source_name in new_articles:
                try:
                    # Check novelty
                    if await self._is_novel_article(title, content):
                        stats["novel"] += 1

                        # Summarize with citations
                        summary = await self._summarize_article(title, content, url)

                        # Add to knowledge base
                        doc_id = hashlib.md5(url.encode()).hexdigest()
                        metadata = {
                            "original_title": title,
                            "source_name": source_name,
                            "discovery_date": datetime.now(timezone.utc).isoformat(),
                        }

                        success = await self.add_document(
                            doc_id=doc_id,
                            content=summary,
                            source=url,
                            metadata=metadata,
                            discovery_type="automated_discovery",
                        )

                        if success:
                            stats["added"] += 1
                        else:
                            stats["errors"] += 1

                except Exception as e:
                    logger.error(f"Error processing article '{title}': {e}")
                    stats["errors"] += 1

            logger.info(
                f"Discovery complete: {stats['fetched']} fetched, "
                f"{stats['novel']} novel, {stats['added']} added"
            )

            return stats

        except Exception as e:
            logger.error(f"Error in knowledge discovery: {e}")
            stats["errors"] += 1
            return stats

    async def _is_novel_article(self, title: str, content: str) -> bool:
        """Check if article is novel using similarity threshold"""
        try:
            full_text = f"{title} {content}"
            results = await self.query_knowledge_base(full_text, top_k=1)

            if not results:
                return True

            closest = results[0]
            distance = closest.get("cosine_distance", 1.0)
            return distance > self.config.novelty_threshold

        except Exception as e:
            logger.error(f"Error checking novelty: {e}")
            return False

    async def _summarize_article(
        self, title: str, content: str, source_url: str
    ) -> str:
        """Summarize article with citations"""
        try:
            max_content_length = 2000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."

            prompt = (
                f"Título: {title}\n"
                f"Conteúdo: {content}\n\n"
                "Resuma os principais achados científicos em 3-5 frases. "
                "Foque em descobertas, inovações e avanços significativos. "
                f"Cite a fonte como [{source_url}].\n\n"
                "Resumo científico:"
            )

            params = {"temperature": 0.25, "max_output_tokens": 256}
            response = self.generation_model.predict(prompt, **params)
            summary = response.text.strip()

            if source_url not in summary:
                summary += f" (Fonte: {source_url})"

            return summary

        except Exception as e:
            logger.error(f"Error summarizing article: {e}")
            return (
                f"Artigo científico: {title} - {content[:200]}... (Fonte: {source_url})"
            )

    async def start_continuous_discovery(self):
        """Start continuous knowledge discovery"""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("Discovery monitoring already running")
            return

        self._monitoring_task = asyncio.create_task(self._discovery_loop())
        logger.info("Started continuous knowledge discovery")

    async def stop_continuous_discovery(self):
        """Stop continuous knowledge discovery"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            logger.info("Stopped continuous knowledge discovery")

    async def _discovery_loop(self):
        """Continuous discovery loop"""
        while True:
            try:
                await self.discover_new_knowledge()
                await asyncio.sleep(self.config.discovery_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        try:
            # Test BigQuery connection
            bq_healthy = True
            try:
                query = f"SELECT COUNT(*) as total FROM `{self.config.project_id}.{self.config.dataset_id}.{self.config.table_id}`"
                query_job = self.bq_client.query(query)
                result = list(query_job.result())
                doc_count = result[0].total if result else 0
            except Exception as e:
                bq_healthy = False
                doc_count = 0
                logger.error(f"BigQuery health check failed: {e}")

            # Test model availability
            models_healthy = True
            try:
                test_embedding = await self.get_embedding("test")
                models_healthy = len(test_embedding) > 0
            except Exception as e:
                models_healthy = False
                logger.error(f"Models health check failed: {e}")

            return {
                "service": "darwin_rag_plus",
                "status": "healthy" if (bq_healthy and models_healthy) else "degraded",
                "components": {
                    "bigquery": {
                        "healthy": bq_healthy,
                        "dataset": self.config.dataset_id,
                        "table": self.config.table_id,
                        "document_count": doc_count,
                    },
                    "vertex_ai": {
                        "healthy": models_healthy,
                        "embedding_model": self.config.embedding_model,
                        "generation_model": self.config.generation_model,
                    },
                    "discovery": {
                        "enabled": self.config.discovery_enabled,
                        "running": self._monitoring_task
                        and not self._monitoring_task.done(),
                        "sources": len(self.sources),
                        "interval_seconds": self.config.discovery_interval,
                    },
                },
                "configuration": {
                    "project_id": self.config.project_id,
                    "location": self.config.location,
                    "novelty_threshold": self.config.novelty_threshold,
                    "max_iterations": self.config.max_iterations,
                    "top_k_retrieval": self.config.top_k_retrieval,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                "service": "darwin_rag_plus",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# Global service instance
_rag_plus_service: Optional[DarwinRAGPlusService] = None


def get_rag_plus_service() -> DarwinRAGPlusService:
    """Get or create RAG++ service instance"""
    global _rag_plus_service
    if _rag_plus_service is None:
        _rag_plus_service = DarwinRAGPlusService()
    return _rag_plus_service


async def initialize_rag_plus_service() -> bool:
    """Initialize RAG++ service for Darwin"""
    try:
        service = get_rag_plus_service()
        await service.get_service_status()  # Health check
        logger.info("Darwin RAG++ Service initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize RAG++ service: {e}")
        return False
