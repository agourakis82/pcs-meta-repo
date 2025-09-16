"""
RAG++ Enhanced Research Agent
=============================

A sophisticated long-horizon reasoning agent that combines:
- Vertex AI for LLM reasoning and embeddings
- BigQuery for vectorized knowledge storage
- ReAct framework for iterative multi-step reasoning
- Continuous scientific discovery monitoring
- Citation-aware knowledge synthesis

This implementation follows the research insights from WebSailor and other
state-of-the-art approaches for complex information-seeking tasks.

Author: PCS-Meta-Repo Team
Date: September 2025
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import vertexai

# Google Cloud imports
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Logging
from loguru import logger
from vertexai.language_models import TextEmbeddingModel, TextGenerationModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.add("rag_agent.log", rotation="500 MB")

@dataclass
class RAGConfig:
    """Configuration for RAG++ system"""
    project_id: str
    location: str = "us-central1"
    dataset_id: str = "knowledge_base"
    table_id: str = "documents"
    embedding_model: str = "textembedding-gecko@001"
    generation_model: str = "text-bison@001"
    novelty_threshold: float = 0.8
    max_iterations: int = 10
    top_k_retrieval: int = 5

class RAGPlusPlusAgent:
    """
    RAG++ Enhanced Research Agent with long-horizon reasoning capabilities.
    
    Implements:
    1. Vector-based knowledge storage in BigQuery
    2. Semantic search and retrieval
    3. ReAct-style iterative reasoning
    4. Continuous knowledge base updates
    5. Citation-aware answer generation
    """
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.seen_ids: set[str] = set()  # Track processed articles
        
        # Initialize Vertex AI
        vertexai.init(project=config.project_id, location=config.location)
        
        # Initialize BigQuery client
        self.bq_client = bigquery.Client(project=config.project_id)
        
        # Initialize models
        self.embedding_model = TextEmbeddingModel.from_pretrained(
            config.embedding_model
        )
        self.generation_model = TextGenerationModel.from_pretrained(
            config.generation_model
        )
        
        # Setup BigQuery knowledge base
        self._setup_bigquery_schema()
        
        logger.info(f"RAG++ Agent initialized with project {config.project_id}")
    
    def _setup_bigquery_schema(self):
        """Setup BigQuery dataset and table for knowledge storage"""
        try:
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
            
            # Define table schema
            schema = [
                bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
                bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="NULLABLE"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE")
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
            logger.error(f"Error setting up BigQuery schema: {e}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using Vertex AI.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        try:
            # Clean and truncate text if needed (models have token limits)
            text = text.strip()[:10000]  # Rough token limit
            
            response = self.embedding_model.get_embeddings([text])
            vector = response[0].values
            return list(vector)
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def add_document(
        self,
        doc_id: str,
        content: str,
        source: str = "",
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Add document to BigQuery knowledge base with embedding.
        
        Args:
            doc_id: Unique identifier for document
            content: Document content/summary
            source: Source URL or reference
            metadata: Additional metadata as JSON
            
        Returns:
            Success status
        """
        try:
            vector = self.get_embedding(content)
            if not vector:
                return False
            
            row = {
                "id": doc_id,
                "content": content,
                "embedding": vector,
                "source": source,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": json.dumps(metadata or {})
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
                logger.info(f"Successfully added document {doc_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            return False

    def query_knowledge_base(
        self, question: str, top_k: int = 5
    ) -> List[Dict[str, str]]:
        """
        Retrieve most semantically relevant documents from BigQuery.
        
        Args:
            question: Search query
            top_k: Number of results to return
            
        Returns:
            List of documents with content, source, and distance
        """
        try:
            q_vector = self.get_embedding(question)
            if not q_vector:
                return []
                
            # Convert vector to string for SQL
            vector_str = ", ".join(map(str, q_vector))
            
            # BigQuery SQL for vector similarity search
            query = f"""
            SELECT 
                content, 
                source,
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
                results.append({
                    "content": row.content,
                    "source": row.source,
                    "cosine_distance": str(row.cosine_distance)
                })
                
            return results
            
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return []
    
    def answer_question(self, question: str) -> str:
        """
        Generate answer using retrieved knowledge and LLM.
        
        Args:
            question: User question
            
        Returns:
            Generated answer with citations
        """
        try:
            # Retrieve relevant documents
            docs = self.query_knowledge_base(question, top_k=self.config.top_k_retrieval)
            
            if not docs:
                return "Desculpe, não encontrei informações relevantes para responder sua pergunta."
            
            # Build context from retrieved documents
            context = ""
            for i, doc in enumerate(docs, 1):
                content = doc.get("content", "")
                source = doc.get("source", "")
                if content:
                    context += f"[{i}] Fonte: {source}\nConteúdo: {content}\n\n"
            
            # Create prompt for LLM
            prompt = (
                f"PERGUNTA: {question}\n\n"
                f"Com base nas seguintes fontes, responda a pergunta de forma "
                f"concisa e cite as fontes utilizadas:\n\n"
                f"{context}\n"
                f"RESPOSTA:"
            )
            
            # Generate response
            params = {"temperature": 0.2, "max_output_tokens": 512}
            response = self.generation_model.predict(prompt, **params)
            answer = response.text.strip()
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Erro ao gerar resposta: {e}"
    
    def answer_question_iterative(self, question: str) -> str:
        """
        Use ReAct loop for multi-step question answering.
        
        Args:
            question: Complex question requiring multi-step reasoning
            
        Returns:
            Final answer after iterative reasoning
        """
        accumulated_info = ""
        
        for step in range(self.config.max_iterations):
            # Construct ReAct prompt
            prompt = (
                "Você é um assistente de pesquisa com acesso a uma base de conhecimento.\n"
                "Sua tarefa é responder a pergunta usando a base de conhecimento. "
                "Você pode BUSCAR na base por mais informações ou dar uma resposta FINAL.\n\n"
                "Formato:\n"
                "Pensamento: <seu raciocínio>\n"
                "Ação: BUSCAR[<consulta>] ou FINAL[<resposta>]\n"
                "Observação: <resultado da ação>\n\n"
                f"Pergunta: {question}\n"
                f"{accumulated_info}\n"
                "Pensamento: "
            )
            
            params = {"temperature": 0.3, "max_output_tokens": 256}
            response = self.generation_model.predict(prompt, **params)
            reaction = response.text.strip()
            
            # Parse model reaction
            if "FINAL[" in reaction:
                # Extract final answer
                start = reaction.find("FINAL[") + 6
                end = reaction.find("]", start)
                if end != -1:
                    answer = reaction[start:end].strip()
                    return answer
                else:
                    return reaction
                    
            elif "BUSCAR[" in reaction:
                # Extract search query
                start = reaction.find("BUSCAR[") + 7
                end = reaction.find("]", start)
                if end != -1:
                    search_query = reaction[start:end].strip()
                    
                    # Perform search
                    results = self.query_knowledge_base(search_query, top_k=3)
                    
                    # Format observations
                    obs_text = ""
                    for res in results:
                        content = res.get("content", "")[:200] + "..."
                        obs_text += f"[Resultado] {content}\n"
                    
                    # Update accumulated info
                    accumulated_info += f"{reaction}\nObservação:\n{obs_text}\n"
                    continue
            else:
                # If format not followed, return what we have
                return reaction
        
        return "Não foi possível chegar a uma resposta conclusiva."

# Initialize with placeholder config - will be loaded from environment
DEFAULT_CONFIG = RAGConfig(
    project_id=os.getenv("GCP_PROJECT_ID", "your-project-id"),
    location=os.getenv("GCP_LOCATION", "us-central1"),
    dataset_id=os.getenv("BQ_DATASET", "knowledge_base"),
    table_id=os.getenv("BQ_TABLE", "documents")
)

if __name__ == "__main__":
    print("RAG++ Enhanced Research Agent - Core Module")
    print("Configure GCP_PROJECT_ID environment variable to initialize")    print("Configure GCP_PROJECT_ID environment variable to initialize")