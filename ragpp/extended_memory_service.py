#!/usr/bin/env python3
"""
Extended Memory Service - RAG++ Persistent Memory System
Sistema de memória extendida para ChatGPT com persistência automática.
"""

import json
import sqlite3
import hashlib
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import threading
import time

# ChromaDB for vector storage
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("❌ ChromaDB not installed. Run: pip install chromadb")

# Sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("❌ Sentence transformers not installed. Run: pip install sentence-transformers")

# Optional encryption (Fernet)
try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None  # type: ignore

@dataclass
class MemoryEntry:
    """Entrada de memória estruturada."""
    id: str
    content: str
    memory_type: str  # 'conversation', 'context', 'project', 'insight', 'reference'
    timestamp: datetime
    tags: List[str]
    metadata: Dict[str, Any]
    importance_score: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('last_accessed'):
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        return cls(**data)

class ExtendedMemoryService:
    """
    Serviço de memória extendida para RAG++.
    
    Features:
    - Armazenamento persistente de conversas e contextos
    - Busca semântica avançada
    - Categorização automática
    - Priorização por importância e frequência de acesso
    - Auto-limpeza de memórias antigas
    - Backup automático
    """
    
    def __init__(self, data_dir: str = "ragpp/data/memory"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Database setup
        self.db_path = self.data_dir / "memory.db"
        self.vector_db_path = self.data_dir / "vector_memory"
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._init_database()
        self._init_vector_store()
        self._init_embeddings()
        self._init_encryption()
        
        # Auto-backup thread
        self.backup_interval = 3600  # 1 hour
        self.backup_thread = None
        self._start_backup_service()

        # Optional auto-cleanup thread
        try:
            self.cleanup_interval = int(os.getenv("MEM_CLEANUP_INTERVAL_SECONDS", "0"))
        except Exception:
            self.cleanup_interval = 0
        self.cleanup_thread = None
        if self.cleanup_interval > 0:
            self._start_cleanup_service()
        
    def _init_database(self):
        """Initialize SQLite database for metadata."""
        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,  -- JSON array
                metadata TEXT,  -- JSON object
                importance_score REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                content_hash TEXT
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                summary TEXT,
                start_time TEXT,
                end_time TEXT,
                message_count INTEGER DEFAULT 0,
                importance_score REAL DEFAULT 0.5,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS project_contexts (
                id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                context_type TEXT,
                content TEXT NOT NULL,
                last_updated TEXT,
                importance_score REAL DEFAULT 0.5,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        # Create indexes
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance_score)")
        
        self.db.commit()
    
    def _init_vector_store(self):
        """Initialize ChromaDB for vector storage."""
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.vector_db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Collections for different memory types
        self.memory_collection = self.chroma_client.get_or_create_collection(
            name="extended_memory",
            metadata={"description": "Extended memory for ChatGPT conversations and contexts"}
        )
        
        self.conversation_collection = self.chroma_client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Full conversation contexts"}
        )
        
        self.project_collection = self.chroma_client.get_or_create_collection(
            name="project_contexts",
            metadata={"description": "Project-specific contexts and insights"}
        )
    
    def _init_embeddings(self):
        """Initialize sentence transformer for embeddings."""
        try:
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            self.logger.info("✅ Sentence transformer loaded")
        except Exception as e:
            self.logger.error(f"❌ Error loading sentence transformer: {e}")
            self.embedder = None

    def _init_encryption(self):
        """Initialize optional Fernet encryption for content at rest."""
        key = os.getenv("MEM_ENCRYPTION_KEY", "").strip()
        if key and Fernet is not None:
            try:
                # Accept raw base64 key or generate from passphrase (not implemented)
                self._fernet = Fernet(key.encode() if not key.startswith("gAAAA") else key)
            except Exception:
                try:
                    self._fernet = Fernet(key)
                except Exception as e:
                    self.logger.warning(f"Encryption key invalid, disabling encryption: {e}")
                    self._fernet = None
        else:
            self._fernet = None

    def _enc(self, text: str) -> str:
        if not self._fernet:
            return text
        try:
            token = self._fernet.encrypt(text.encode("utf-8"))
            return token.decode("utf-8")
        except Exception:
            return text

    def _dec(self, text: str) -> str:
        if not self._fernet:
            return text
        try:
            # Some docs may be plain if created before encryption
            token = text.encode("utf-8")
            plain = self._fernet.decrypt(token)
            return plain.decode("utf-8")
        except Exception:
            return text
    
    def _start_backup_service(self):
        """Start automatic backup service."""
        def backup_worker():
            while True:
                try:
                    time.sleep(self.backup_interval)
                    self.create_backup()
                except Exception as e:
                    self.logger.error(f"Backup error: {e}")
        
        self.backup_thread = threading.Thread(target=backup_worker, daemon=True)
        self.backup_thread.start()
        self.logger.info("🔄 Auto-backup service started")

    def _start_cleanup_service(self):
        """Start automatic cleanup service for old/low-importance memories."""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(max(600, self.cleanup_interval))
                    days = int(os.getenv("MEM_RETENTION_DAYS", "90"))
                    self.cleanup_old_memories(days_to_keep=days)
                except Exception as e:
                    self.logger.error(f"Cleanup error: {e}")
        self.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        self.logger.info("🧹 Auto-cleanup service started")
    
    def store_memory(self, 
                    content: str, 
                    memory_type: str = "general",
                    tags: List[str] = None,
                    metadata: Dict[str, Any] = None,
                    importance_score: float = 0.5) -> str:
        """
        Armazena uma nova memória.
        
        Args:
            content: Conteúdo da memória
            memory_type: Tipo (conversation, context, project, insight, reference)
            tags: Tags para categorização
            metadata: Metadados adicionais
            importance_score: Pontuação de importância (0-1)
        
        Returns:
            ID da memória armazenada
        """
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}
        
        # Generate unique ID
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        memory_id = f"{memory_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content_hash}"
        
        # Create memory entry
        memory = MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            tags=tags,
            metadata=metadata,
            importance_score=importance_score
        )
        
        # Store in database
        self.db.execute("""
            INSERT OR REPLACE INTO memories 
            (id, content, memory_type, timestamp, tags, metadata, importance_score, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory.id,
            self._enc(memory.content),
            memory.memory_type,
            memory.timestamp.isoformat(),
            json.dumps(memory.tags),
            json.dumps(memory.metadata),
            memory.importance_score,
            content_hash
        ))
        self.db.commit()
        
        # Store in vector database
        if self.embedder:
            try:
                embedding = self.embedder.encode([content])[0].tolist()
                self.memory_collection.upsert(
                    ids=[memory_id],
                    embeddings=[embedding],
                    metadatas=[{
                        "memory_type": memory_type,
                        "timestamp": memory.timestamp.isoformat(),
                        "importance_score": importance_score,
                        "tags": json.dumps(tags)
                    }],
                    documents=[self._enc(content)]
                )
            except Exception as e:
                self.logger.error(f"Error storing vector: {e}")
        
        self.logger.info(f"✅ Memory stored: {memory_id}")
        return memory_id
    
    def store_conversation(self, 
                          conversation_data: Dict[str, Any],
                          title: str = None,
                          importance_score: float = 0.5) -> str:
        """
        Armazena uma conversa completa.
        
        Args:
            conversation_data: Dados da conversa (mensagens, contexto, etc.)
            title: Título da conversa
            importance_score: Importância da conversa
        
        Returns:
            ID da conversa
        """
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Extract or generate title
        if not title:
            # Try to extract from first user message
            messages = conversation_data.get('messages', [])
            if messages:
                first_msg = next((m for m in messages if m.get('role') == 'user'), None)
                if first_msg:
                    title = first_msg.get('content', '')[:100] + "..."
            if not title:
                title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Generate summary
        summary = self._generate_conversation_summary(conversation_data)
        
        # Store conversation metadata
        self.db.execute("""
            INSERT OR REPLACE INTO conversations
            (id, title, summary, start_time, message_count, importance_score, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            conversation_id,
            title,
            summary,
            datetime.now().isoformat(),
            len(conversation_data.get('messages', [])),
            importance_score,
            json.dumps(conversation_data)
        ))
        self.db.commit()
        
        # Store full conversation in vector database
        if self.embedder:
            try:
                conv_text = self._conversation_to_text(conversation_data)
                embedding = self.embedder.encode([conv_text])[0].tolist()
                
                self.conversation_collection.upsert(
                    ids=[conversation_id],
                    embeddings=[embedding],
                    metadatas=[{
                        "title": title,
                        "start_time": datetime.now().isoformat(),
                        "message_count": len(conversation_data.get('messages', [])),
                        "importance_score": importance_score
                    }],
                    documents=[self._enc(conv_text)]
                )
            except Exception as e:
                self.logger.error(f"Error storing conversation vector: {e}")
        
        self.logger.info(f"✅ Conversation stored: {conversation_id}")
        return conversation_id
    
    def store_project_context(self,
                             project_name: str,
                             context_type: str,
                             content: str,
                             metadata: Dict[str, Any] = None) -> str:
        """
        Armazena contexto específico do projeto.
        
        Args:
            project_name: Nome do projeto
            context_type: Tipo de contexto (status, decisions, issues, plans)
            content: Conteúdo do contexto
            metadata: Metadados adicionais
        
        Returns:
            ID do contexto
        """
        if metadata is None:
            metadata = {}
        
        context_id = f"ctx_{project_name}_{context_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store in database
        self.db.execute("""
            INSERT OR REPLACE INTO project_contexts
            (id, project_name, context_type, content, last_updated, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            context_id,
            project_name,
            context_type,
            content,
            datetime.now().isoformat(),
            json.dumps(metadata)
        ))
        self.db.commit()
        
        # Store in vector database
        if self.embedder:
            try:
                embedding = self.embedder.encode([content])[0].tolist()
                self.project_collection.upsert(
                    ids=[context_id],
                    embeddings=[embedding],
                    metadatas=[{
                        "project_name": project_name,
                        "context_type": context_type,
                        "last_updated": datetime.now().isoformat()
                    }],
                    documents=[content]
                )
            except Exception as e:
                self.logger.error(f"Error storing project context vector: {e}")
        
        self.logger.info(f"✅ Project context stored: {context_id}")
        return context_id
    
    def search_memory(self, 
                     query: str, 
                     memory_types: List[str] = None,
                     max_results: int = 10,
                     importance_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Busca na memória usando busca semântica.
        
        Args:
            query: Consulta de busca
            memory_types: Tipos de memória para filtrar
            max_results: Número máximo de resultados
            importance_threshold: Limiar mínimo de importância
        
        Returns:
            Lista de memórias relevantes
        """
        results = []
        
        if not self.embedder:
            self.logger.warning("No embedder available for semantic search")
            return results
        
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode([query])[0].tolist()
            
            # Search in memory collection
            search_results = self.memory_collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results * 2,  # Get more to filter
                include=['metadatas', 'documents', 'distances']
            )
            
            # Process results
            for i, doc_id in enumerate(search_results['ids'][0]):
                metadata = search_results['metadatas'][0][i]
                content = self._dec(search_results['documents'][0][i])
                distance = search_results['distances'][0][i]
                
                # Filter by memory type
                if memory_types and metadata.get('memory_type') not in memory_types:
                    continue
                
                # Filter by importance
                if metadata.get('importance_score', 0) < importance_threshold:
                    continue
                
                # Get additional info from database
                cursor = self.db.execute(
                    "SELECT * FROM memories WHERE id = ?", (doc_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    # Update access count
                    self.db.execute(
                        "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                        (datetime.now().isoformat(), doc_id)
                    )
                    
                    results.append({
                        'id': doc_id,
                        'content': content,
                        'memory_type': metadata.get('memory_type'),
                        'importance_score': metadata.get('importance_score'),
                        'relevance_score': 1.0 - distance,  # Convert distance to relevance
                        'tags': json.loads(row[4] or '[]'),
                        'metadata': json.loads(row[5] or '{}'),
                        'access_count': row[7],
                        'timestamp': metadata.get('timestamp')
                    })
            
            self.db.commit()

            # Also search in conversations if requested or unspecified types
            include_conversations = (not memory_types) or ("conversation" in (memory_types or []))
            if include_conversations:
                try:
                    conv_results = self.conversation_collection.query(
                        query_embeddings=[query_embedding],
                        n_results=max_results,
                        include=['metadatas', 'documents', 'distances']
                    )
                    for i, conv_id in enumerate(conv_results['ids'][0]):
                        meta = conv_results['metadatas'][0][i]
                        conv_text = self._dec(conv_results['documents'][0][i])
                        dist = conv_results['distances'][0][i]
                        results.append({
                            'id': conv_id,
                            'content': conv_text,
                            'memory_type': 'conversation',
                            'importance_score': meta.get('importance_score', 0.5),
                            'relevance_score': 1.0 - dist,
                            'tags': [],
                            'metadata': meta,
                            'access_count': 0,
                            'timestamp': meta.get('start_time')
                        })
                except Exception as e:
                    self.logger.error(f"Error in conversation search: {e}")
            
            # Sort by relevance and importance
            results.sort(key=lambda x: (x['relevance_score'] + x['importance_score']) / 2, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error in memory search: {e}")
        
        return results[:max_results]
    
    def get_recent_memories(self, 
                           days: int = 7,
                           memory_types: List[str] = None,
                           max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Recupera memórias recentes.
        
        Args:
            days: Número de dias para buscar
            memory_types: Tipos de memória para filtrar
            max_results: Número máximo de resultados
        
        Returns:
            Lista de memórias recentes
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = """
            SELECT * FROM memories 
            WHERE timestamp > ?
        """
        params = [cutoff_date]
        
        if memory_types:
            placeholders = ','.join('?' * len(memory_types))
            query += f" AND memory_type IN ({placeholders})"
            params.extend(memory_types)
        
        query += " ORDER BY importance_score DESC, timestamp DESC LIMIT ?"
        params.append(max_results)
        
        cursor = self.db.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'content': self._dec(row[1] or ''),
                'memory_type': row[2],
                'timestamp': row[3],
                'tags': json.loads(row[4] or '[]'),
                'metadata': json.loads(row[5] or '{}'),
                'importance_score': row[6],
                'access_count': row[7]
            })
        
        return results
    
    def get_project_status(self, project_name: str = "pcs-meta-repo") -> Dict[str, Any]:
        """
        Recupera status atual do projeto.
        
        Args:
            project_name: Nome do projeto
        
        Returns:
            Status completo do projeto
        """
        # Get latest project contexts
        cursor = self.db.execute("""
            SELECT * FROM project_contexts 
            WHERE project_name = ? 
            ORDER BY last_updated DESC
        """, (project_name,))
        
        contexts = []
        for row in cursor.fetchall():
            contexts.append({
                'id': row[0],
                'context_type': row[2],
                'content': row[3],
                'last_updated': row[4],
                'metadata': json.loads(row[6] or '{}')
            })
        
        # Get recent conversations
        recent_convs = self.db.execute("""
            SELECT id, title, summary, start_time FROM conversations
            ORDER BY start_time DESC LIMIT 5
        """).fetchall()
        
        # Get memory statistics
        stats = self.db.execute("""
            SELECT 
                memory_type,
                COUNT(*) as count,
                AVG(importance_score) as avg_importance
            FROM memories 
            GROUP BY memory_type
        """).fetchall()
        
        return {
            'project_name': project_name,
            'last_updated': datetime.now().isoformat(),
            'contexts': contexts,
            'recent_conversations': [
                {
                    'id': row[0],
                    'title': row[1],
                    'summary': row[2],
                    'start_time': row[3]
                } for row in recent_convs
            ],
            'memory_stats': [
                {
                    'type': row[0],
                    'count': row[1],
                    'avg_importance': row[2]
                } for row in stats
            ]
        }
    
    def _generate_conversation_summary(self, conversation_data: Dict[str, Any]) -> str:
        """Generate summary of conversation."""
        messages = conversation_data.get('messages', [])
        if not messages:
            return "Empty conversation"
        
        # Simple summary based on first and last messages
        first_msg = next((m for m in messages if m.get('role') == 'user'), None)
        last_msg = messages[-1] if messages else None
        
        summary_parts = []
        if first_msg:
            summary_parts.append(f"Started with: {first_msg.get('content', '')[:100]}")
        if last_msg and last_msg != first_msg:
            summary_parts.append(f"Ended with: {last_msg.get('content', '')[:100]}")
        
        return " | ".join(summary_parts)
    
    def _conversation_to_text(self, conversation_data: Dict[str, Any]) -> str:
        """Convert conversation to searchable text."""
        messages = conversation_data.get('messages', [])
        text_parts = []
        
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            text_parts.append(f"{role}: {content}")
        
        return "\n".join(text_parts)
    
    def create_backup(self) -> str:
        """Create backup of memory database."""
        backup_dir = self.data_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f"memory_backup_{timestamp}.db"
        
        try:
            # Backup SQLite database
            backup_db = sqlite3.connect(backup_path)
            self.db.backup(backup_db)
            backup_db.close()
            
            # Also backup vector database
            vector_backup_path = backup_dir / f"vector_backup_{timestamp}"
            import shutil
            shutil.copytree(self.vector_db_path, vector_backup_path, dirs_exist_ok=True)
            
            self.logger.info(f"✅ Backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            self.logger.error(f"❌ Backup failed: {e}")
            return ""
    
    def cleanup_old_memories(self, days_to_keep: int = 90):
        """Clean up old, low-importance memories."""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        # Delete low-importance, old memories
        cursor = self.db.execute("""
            DELETE FROM memories 
            WHERE timestamp < ? AND importance_score < 0.3 AND access_count < 2
        """, (cutoff_date,))
        
        deleted_count = cursor.rowcount
        self.db.commit()
        
        self.logger.info(f"🧹 Cleaned up {deleted_count} old memories")
        return deleted_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory service statistics."""
        # Memory counts
        memory_stats = self.db.execute("""
            SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type
        """).fetchall()
        
        # Total memories
        total_memories = sum(count for _, count in memory_stats)
        
        # Recent activity
        recent_count = self.db.execute("""
            SELECT COUNT(*) FROM memories WHERE timestamp > ?
        """, ((datetime.now() - timedelta(days=7)).isoformat(),)).fetchone()[0]
        
        return {
            'total_memories': total_memories,
            'recent_memories_7d': recent_count,
            'memory_by_type': dict(memory_stats),
            'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
            'vector_db_exists': os.path.exists(self.vector_db_path),
            'last_backup': self._get_last_backup_time()
        }
    
    def _get_last_backup_time(self) -> str:
        """Get timestamp of last backup."""
        backup_dir = self.data_dir / "backups"
        if not backup_dir.exists():
            return "Never"
        
        backups = list(backup_dir.glob("memory_backup_*.db"))
        if not backups:
            return "Never"
        
        latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
        return datetime.fromtimestamp(latest_backup.stat().st_mtime).isoformat()

# Global memory service instance
_memory_service = None

def get_memory_service() -> ExtendedMemoryService:
    """Get global memory service instance."""
    global _memory_service
    if _memory_service is None:
        _memory_service = ExtendedMemoryService()
    return _memory_service

if __name__ == "__main__":
    # Demo usage
    memory = ExtendedMemoryService()
    
    # Store some test memories
    print("🧠 Testing Extended Memory Service")
    
    # Store project context
    memory.store_project_context(
        project_name="pcs-meta-repo",
        context_type="status",
        content="RAG++ system is fully operational with 168 papers indexed. ChatGPT connector configured and working.",
        metadata={"components": ["RAG++", "ChatGPT", "MCP"], "status": "operational"}
    )
    
    # Store conversation
    sample_conversation = {
        "messages": [
            {"role": "user", "content": "Como configurar o RAG++ para ChatGPT?"},
            {"role": "assistant", "content": "Configurei um sistema completo com Custom Actions, Custom GPT e MCP server..."},
            {"role": "user", "content": "Perfeito! Agora quero que inicie automaticamente."}
        ],
        "context": "Configuration session for RAG++ ChatGPT integration"
    }
    
    conv_id = memory.store_conversation(
        sample_conversation,
        title="RAG++ ChatGPT Configuration",
        importance_score=0.8
    )
    
    # Test search
    results = memory.search_memory("RAG++ configuration ChatGPT")
    print(f"Found {len(results)} relevant memories")
    
    # Get stats
    stats = memory.get_stats()
    print(f"Memory Stats: {stats}")
    
    print("✅ Extended Memory Service test complete!")
