"""Darwin Platform Comprehensive Test Suite

Tests for all Darwin platform components including:
- RAG backends and services  
- Security and rate limiting
- Memory storage and search
- Tree-search algorithms
- Score contracts execution
- Context caching system
"""

import asyncio
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from api.routers.memory import MemoryStorage, SessionLogEntry
from api.security import RateLimiter, TokenBucket
from services.context_cache import ContextCache, analyze_prompt_caching
from services.rag_vertex import (
    RagResponse,
    VertexRagEngineBackend,
    VertexVectorBackend,
    get_rag,
)
from services.score_contracts import (
    ContractSandbox,
    DeltaKecV1Contract,
    EditorialV1Contract,
    ZucoReadingV1Contract,
)

# Test imports
from services.settings import DarwinSettings
from services.tree_search import TestStateEvaluator, TreeNode, TreeSearch


class TestDarwinSettings:
    """Test Darwin platform settings configuration."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = DarwinSettings()
        
        assert settings.PROJECT_ID == "darwin-platform"
        assert settings.BASE_URL == "https://darwin-platform.run.app"
        assert settings.RAG_ENGINE_ENABLED is True
        assert settings.VECTOR_SEARCH_ENABLED is True
        assert settings.CONTEXT_CACHE_ENABLED is True
        assert settings.RATE_LIMIT_REQUESTS == 100
        assert settings.RATE_LIMIT_WINDOW == 60
    
    @patch.dict(os.environ, {
        'PROJECT_ID': 'test-project',
        'BASE_URL': 'https://test.example.com',
        'OPENAI_VERIFICATION_TOKEN': 'test-token'
    })
    def test_environment_override(self):
        """Test environment variable override."""
        settings = DarwinSettings()
        
        assert settings.PROJECT_ID == "test-project"
        assert settings.BASE_URL == "https://test.example.com"
        assert settings.OPENAI_VERIFICATION_TOKEN == "test-token"


class TestVertexRagBackends:
    """Test Vertex AI RAG backends."""
    
    @pytest.fixture
    def mock_vertex_client(self):
        """Mock Vertex AI client."""
        with patch('services.rag_vertex.aiplatform') as mock_ai:
            mock_client = Mock()
            mock_ai.init.return_value = None
            yield mock_client
    
    def test_rag_engine_backend_init(self, mock_vertex_client):
        """Test RAG Engine backend initialization."""
        backend = VertexRagEngineBackend(
            project_id="test-project",
            location="us-central1",
            engine_id="test-engine"
        )
        
        assert backend.project_id == "test-project"
        assert backend.location == "us-central1"
        assert backend.engine_id == "test-engine"
        assert backend.backend_type == "rag_engine"
    
    @pytest.mark.asyncio
    async def test_rag_engine_query(self, mock_vertex_client):
        """Test RAG Engine query processing."""
        backend = VertexRagEngineBackend(
            project_id="test-project",
            location="us-central1",
            engine_id="test-engine"
        )
        
        # Mock response
        mock_response = Mock()
        mock_response.response = "Test answer"
        mock_response.source_data = [
            Mock(title="Test Doc", url="http://test.com", content="Test content")
        ]
        
        with patch.object(backend, '_get_rag_client') as mock_client_getter:
            mock_client = Mock()
            mock_client.query.return_value = mock_response
            mock_client_getter.return_value = mock_client
            
            result = await backend.query("test query")
            
            assert isinstance(result, RagResponse)
            assert result.answer == "Test answer"
            assert len(result.sources) == 1
            assert result.sources[0].title == "Test Doc"
    
    def test_vector_backend_init(self, mock_vertex_client):
        """Test Vector Search backend initialization."""
        backend = VertexVectorBackend(
            project_id="test-project",
            location="us-central1",
            index_endpoint="test-endpoint"
        )
        
        assert backend.project_id == "test-project"
        assert backend.location == "us-central1" 
        assert backend.index_endpoint == "test-endpoint"
        assert backend.backend_type == "vector_search"
    
    @pytest.mark.asyncio
    async def test_vector_backend_health_check(self, mock_vertex_client):
        """Test Vector Search backend health check."""
        backend = VertexVectorBackend(
            project_id="test-project",
            location="us-central1",
            index_endpoint="test-endpoint"
        )
        
        with patch.object(backend, '_get_vector_client') as mock_client_getter:
            mock_client = Mock()
            mock_client_getter.return_value = mock_client
            
            health = await backend.health_check()
            
            assert health.backend_type == "vector_search"
            assert health.healthy is True


class TestSecurity:
    """Test security and rate limiting."""
    
    def test_token_bucket_init(self):
        """Test token bucket initialization."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        
        assert bucket.capacity == 10
        assert bucket.tokens == 10
        assert bucket.refill_rate == 1.0
    
    def test_token_bucket_consume(self):
        """Test token consumption."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        
        # Should allow consumption
        assert bucket.consume(5) is True
        assert bucket.tokens == 5
        
        # Should deny overconsumption
        assert bucket.consume(10) is False
        assert bucket.tokens == 5
    
    def test_rate_limiter_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(
            requests_per_window=100,
            window_seconds=60
        )
        
        assert limiter.requests_per_window == 100
        assert limiter.window_seconds == 60
        assert len(limiter.buckets) == 0
    
    def test_rate_limiter_check_limit(self):
        """Test rate limit checking."""
        limiter = RateLimiter(
            requests_per_window=2,
            window_seconds=60
        )
        
        # Should allow first requests
        assert limiter.check_limit("test_key") is True
        assert limiter.check_limit("test_key") is True
        
        # Should deny third request
        assert limiter.check_limit("test_key") is False


class TestMemoryStorage:
    """Test memory storage and search."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_memory_storage_init(self, temp_storage_dir):
        """Test memory storage initialization."""
        storage = MemoryStorage(storage_dir=temp_storage_dir)
        
        assert storage.storage_dir == Path(temp_storage_dir)
        assert storage.jsonl_file.exists()
        assert storage.db_file.exists()
    
    @pytest.mark.asyncio
    async def test_log_session_entry(self, temp_storage_dir):
        """Test session logging."""
        storage = MemoryStorage(storage_dir=temp_storage_dir)
        
        entry = SessionLogEntry(
            session_id="test-session",
            timestamp=datetime.now(timezone.utc),
            query="test query",
            response="test response",
            metadata={"test": "value"}
        )
        
        result = await storage.log_session_entry(entry)
        
        assert result["status"] == "logged"
        assert result["entry_id"] is not None
        assert result["storage_locations"] == ["jsonl", "sqlite"]
    
    @pytest.mark.asyncio
    async def test_search_sessions(self, temp_storage_dir):
        """Test session search."""
        storage = MemoryStorage(storage_dir=temp_storage_dir)
        
        # Log test entry
        entry = SessionLogEntry(
            session_id="test-session",
            timestamp=datetime.now(timezone.utc),
            query="machine learning query",
            response="ML response",
            metadata={}
        )
        await storage.log_session_entry(entry)
        
        # Mock RAG backend for search
        with patch.object(storage, 'rag_backend') as mock_rag:
            mock_response = RagResponse(
                answer="Search result",
                sources=[],
                metadata={"query": "test"}
            )
            mock_rag.query.return_value = mock_response
            
            results = await storage.search_sessions(
                query="machine learning",
                session_id="test-session"
            )
            
            assert results["total_results"] >= 0
            assert "rag_response" in results


class TestTreeSearch:
    """Test tree search algorithms."""
    
    def test_tree_node_init(self):
        """Test tree node initialization."""
        node = TreeNode(state="test_state")
        
        assert node.state == "test_state"
        assert node.visits == 0
        assert node.value == 0.0
        assert len(node.children) == 0
        assert node.parent is None
    
    def test_tree_node_add_child(self):
        """Test adding child nodes."""
        parent = TreeNode(state="parent")
        child = TreeNode(state="child")
        
        parent.add_child("action", child)
        
        assert "action" in parent.children
        assert parent.children["action"] == child
        assert child.parent == parent
    
    def test_tree_node_update(self):
        """Test node value updates."""
        node = TreeNode(state="test")
        
        node.update(0.8)
        
        assert node.visits == 1
        assert node.value == 0.8
        
        node.update(0.6)
        
        assert node.visits == 2
        assert node.value == 0.7  # Average of 0.8 and 0.6
    
    def test_tree_node_puct_score(self):
        """Test PUCT score calculation."""
        parent = TreeNode(state="parent")
        parent.visits = 10
        
        child = TreeNode(state="child")
        child.visits = 2
        child.value = 0.6
        
        parent.add_child("action", child)
        
        score = child.puct_score(c_puct=1.0)
        
        # PUCT = Q + c_puct * sqrt(ln(N_parent) / N_child)
        import math
        expected = 0.6 + 1.0 * math.sqrt(math.log(10) / 2)
        
        assert abs(score - expected) < 1e-6
    
    @pytest.mark.asyncio
    async def test_tree_search_init(self):
        """Test tree search initialization."""
        evaluator = TestStateEvaluator()
        search = TreeSearch(evaluator=evaluator)
        
        assert search.evaluator == evaluator
        assert search.root is None
    
    @pytest.mark.asyncio
    async def test_tree_search_run(self):
        """Test tree search execution."""
        evaluator = TestStateEvaluator()
        search = TreeSearch(evaluator=evaluator)
        
        result = await search.search(
            initial_state="initial",
            num_simulations=10,
            max_depth=3
        )
        
        assert result is not None
        assert "best_action" in result
        assert "value" in result
        assert "num_simulations" in result
        assert result["num_simulations"] == 10


class TestScoreContracts:
    """Test score contracts execution."""
    
    def test_delta_kec_contract_init(self):
        """Test Delta KEC contract initialization."""
        contract = DeltaKecV1Contract()
        
        assert contract.contract_type == "delta_kec_v1"
        assert contract.version == "1.0"
        assert contract.description is not None
    
    @pytest.mark.asyncio
    async def test_delta_kec_execution(self):
        """Test Delta KEC contract execution."""
        contract = DeltaKecV1Contract()
        
        data = {
            "knowledge_vectors": [
                {"entropy": 2.5, "mutual_info": 0.8},
                {"entropy": 3.0, "mutual_info": 1.2}
            ],
            "interaction_weight": 0.7,
            "temporal_decay": 0.9
        }
        
        result = await contract.execute(data)
        
        assert result["success"] is True
        assert "delta_kec_score" in result
        assert isinstance(result["delta_kec_score"], (int, float))
        assert 0 <= result["delta_kec_score"] <= 1
    
    def test_zuco_reading_contract_init(self):
        """Test ZuCo Reading contract initialization."""
        contract = ZucoReadingV1Contract()
        
        assert contract.contract_type == "zuco_reading_v1"
        assert contract.version == "1.0"
        assert contract.description is not None
    
    @pytest.mark.asyncio
    async def test_zuco_reading_execution(self):
        """Test ZuCo Reading contract execution."""
        contract = ZucoReadingV1Contract()
        
        data = {
            "eeg_features": {
                "theta_power": 0.6,
                "alpha_power": 0.7,
                "beta_power": 0.5,
                "gamma_power": 0.4
            },
            "eye_tracking": {
                "fixation_duration": 250,
                "saccade_amplitude": 3.5,
                "regression_rate": 0.15
            },
            "text_complexity": {
                "word_frequency": 0.8,
                "syntactic_complexity": 0.6
            }
        }
        
        result = await contract.execute(data)
        
        assert result["success"] is True
        assert "cognitive_load_score" in result
        assert isinstance(result["cognitive_load_score"], (int, float))
    
    def test_editorial_contract_init(self):
        """Test Editorial contract initialization."""
        contract = EditorialV1Contract()
        
        assert contract.contract_type == "editorial_v1"
        assert contract.version == "1.0"
        assert contract.description is not None
    
    @pytest.mark.asyncio
    async def test_editorial_execution(self):
        """Test Editorial contract execution."""
        contract = EditorialV1Contract()
        
        data = {
            "text": "This is a sample text for editorial analysis.",
            "metrics": {
                "readability_score": 0.7,
                "grammar_score": 0.9,
                "vocabulary_richness": 0.6,
                "coherence_score": 0.8
            },
            "style_preferences": {
                "formality": "medium",
                "target_audience": "general"
            }
        }
        
        result = await contract.execute(data)
        
        assert result["success"] is True
        assert "editorial_score" in result
        assert isinstance(result["editorial_score"], (int, float))
    
    @pytest.mark.asyncio
    async def test_contract_sandbox_execution(self):
        """Test sandboxed contract execution."""
        sandbox = ContractSandbox(timeout_seconds=5)
        contract = DeltaKecV1Contract()
        
        data = {
            "knowledge_vectors": [
                {"entropy": 2.0, "mutual_info": 0.5}
            ],
            "interaction_weight": 0.5,
            "temporal_decay": 1.0
        }
        
        result = await sandbox.execute_contract(contract, data)
        
        assert result["success"] is True
        assert result["execution_time"] > 0
        assert "contract_result" in result
    
    @pytest.mark.asyncio
    async def test_contract_sandbox_timeout(self):
        """Test contract execution timeout."""
        sandbox = ContractSandbox(timeout_seconds=0.1)
        
        # Create a mock contract that takes too long
        class SlowContract:
            contract_type = "slow_test"
            version = "1.0"
            
            async def execute(self, data):
                await asyncio.sleep(1)  # Longer than timeout
                return {"success": True}
        
        contract = SlowContract()
        
        result = await sandbox.execute_contract(contract, {})
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()


class TestContextCache:
    """Test context caching system."""
    
    def test_context_cache_init(self):
        """Test context cache initialization."""
        cache = ContextCache(max_cache_size=100)
        
        assert cache.max_cache_size == 100
        assert len(cache.cache) == 0
        assert len(cache.prefix_stats) == 0
    
    def test_compute_cache_key(self):
        """Test cache key computation."""
        cache = ContextCache()
        
        key1 = cache.compute_cache_key("test prefix", "model1")
        key2 = cache.compute_cache_key("test prefix", "model1")
        key3 = cache.compute_cache_key("test prefix", "model2")
        
        # Same prefix and model should produce same key
        assert key1 == key2
        # Different model should produce different key
        assert key1 != key3
        # Key should be 16 characters (truncated SHA256)
        assert len(key1) == 16
    
    def test_find_stable_prefix(self):
        """Test stable prefix detection."""
        cache = ContextCache()
        
        # Test with common system prompt pattern
        prompt = "You are an expert assistant.\n\nUser: What is AI?"
        prefix = cache._find_stable_prefix(prompt)
        
        assert prefix is not None
        assert "You are an expert assistant." in prefix
    
    def test_analyze_prompt(self):
        """Test prompt analysis."""
        cache = ContextCache()
        
        prompt = "You are a helpful assistant.\n\nUser: Hello world!"
        prefix, suffix, cache_available = cache.analyze_prompt(prompt)
        
        assert prefix is not None
        assert "You are a helpful assistant." in prefix
        assert "User: Hello world!" in suffix
        assert cache_available is False  # First time seeing this prefix
    
    def test_cache_prefix(self):
        """Test prefix caching."""
        cache = ContextCache()
        
        prefix = "You are a helpful assistant."
        cache_key = cache.cache_prefix(prefix)
        
        assert cache_key in cache.cache
        assert cache.cache[cache_key].prefix == prefix
        assert cache.cache[cache_key].hit_count == 0
    
    def test_get_cached_prompt(self):
        """Test cached prompt retrieval."""
        cache = ContextCache()
        
        prefix = "You are a helpful assistant."
        cache_key = cache.cache_prefix(prefix)
        
        result = cache.get_cached_prompt(cache_key, "New user query")
        
        assert result is not None
        cached_prefix, full_prompt = result
        assert cached_prefix == prefix
        assert "New user query" in full_prompt
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = ContextCache()
        
        # Add some cache entries
        cache.cache_prefix("prefix1")
        cache.cache_prefix("prefix2")
        
        stats = cache.get_cache_stats()
        
        assert stats["total_entries"] == 2
        assert isinstance(stats["hit_ratio"], float)
        assert isinstance(stats["cache_utilization"], float)
    
    def test_analyze_prompt_caching_function(self):
        """Test standalone prompt caching analysis."""
        prompt = "You are an AI assistant.\n\nAnalyze this text."
        
        result = analyze_prompt_caching(prompt)
        
        assert "cacheable" in result
        assert "cache_available" in result
        assert "recommendations" in result
        assert "estimated_savings" in result


class TestIntegration:
    """Integration tests for Darwin platform."""
    
    @pytest.mark.asyncio
    async def test_rag_backend_factory(self):
        """Test RAG backend factory function."""
        with patch('services.rag_vertex.get_settings') as mock_settings:
            settings = Mock()
            settings.RAG_ENGINE_ENABLED = True
            settings.VECTOR_SEARCH_ENABLED = False
            settings.PROJECT_ID = "test-project"
            settings.LOCATION = "us-central1"
            settings.RAG_ENGINE_ID = "test-engine"
            mock_settings.return_value = settings
            
            backend = get_rag()
            
            assert isinstance(backend, VertexRagEngineBackend)
            assert backend.project_id == "test-project"
    
    @pytest.mark.asyncio
    async def test_memory_with_rag_integration(self, temp_storage_dir):
        """Test memory storage with RAG integration."""
        storage = MemoryStorage(storage_dir=temp_storage_dir)
        
        # Mock RAG backend
        mock_rag = Mock()
        mock_response = RagResponse(
            answer="Integrated answer",
            sources=[],
            metadata={}
        )
        mock_rag.query.return_value = mock_response
        storage.rag_backend = mock_rag
        
        # Log an entry
        entry = SessionLogEntry(
            session_id="integration-test",
            timestamp=datetime.now(timezone.utc),
            query="integration query",
            response="integration response",
            metadata={}
        )
        await storage.log_session_entry(entry)
        
        # Search using RAG
        results = await storage.search_sessions(
            query="integration",
            session_id="integration-test"
        )
        
        assert "rag_response" in results
        assert results["rag_response"]["answer"] == "Integrated answer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])    pytest.main([__file__, "-v"])