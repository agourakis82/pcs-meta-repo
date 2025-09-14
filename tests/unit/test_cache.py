# -*- coding: utf-8 -*-
"""
Testes unitários para o sistema de cache.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from api.cache import CacheManager, MemoryCache, RedisCache


class TestMemoryCache:
    """Testes para cache em memória."""

    def test_memory_cache_init(self):
        """Testa inicialização do cache em memória."""
        cache = MemoryCache(max_size=100, default_ttl=3600)
        assert cache.max_size == 100
        assert cache.default_ttl == 3600
        assert len(cache._cache) == 0

    @pytest.mark.asyncio
    async def test_memory_cache_set_get(self):
        """Testa operações básicas de set/get."""
        cache = MemoryCache()
        
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_memory_cache_get_nonexistent(self):
        """Testa get de chave inexistente."""
        cache = MemoryCache()
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_memory_cache_delete(self):
        """Testa deleção de chave."""
        cache = MemoryCache()
        
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"
        
        deleted = await cache.delete("key1")
        assert deleted is True
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_memory_cache_delete_nonexistent(self):
        """Testa deleção de chave inexistente."""
        cache = MemoryCache()
        result = await cache.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_memory_cache_clear(self):
        """Testa limpeza do cache."""
        cache = MemoryCache()
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        await cache.clear()
        assert len(cache._cache) == 0
        result1 = await cache.get("key1")
        result2 = await cache.get("key2")
        assert result1 is None
        assert result2 is None

    @pytest.mark.asyncio
    async def test_memory_cache_ttl_with_custom_value(self):
        """Testa definição de TTL customizado."""
        cache = MemoryCache(default_ttl=3600)
        
        # Set com TTL customizado de 1 segundo
        await cache.set("key1", "value1", ttl=1)
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_memory_cache_max_size_behavior(self):
        """Testa comportamento com tamanho máximo."""
        cache = MemoryCache(max_size=2)
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        # Adicionar terceira chave deve ativar LRU
        await cache.set("key3", "value3")
        
        # key1 deve ter sido removida (LRU)
        result1 = await cache.get("key1")
        result2 = await cache.get("key2")
        result3 = await cache.get("key3")
        
        assert result1 is None  # Removida por LRU
        assert result2 == "value2"
        assert result3 == "value3"

    @pytest.mark.asyncio
    async def test_memory_cache_get_stats(self):
        """Testa estatísticas do cache."""
        cache = MemoryCache()
        
        # Hit
        await cache.set("key1", "value1")
        await cache.get("key1")
        
        # Miss
        await cache.get("nonexistent")
        
        stats = await cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.cache_size == 1
        assert stats.memory_usage > 0

    @pytest.mark.asyncio
    async def test_memory_cache_invalidate_by_tags(self):
        """Testa invalidação por tags."""
        cache = MemoryCache()
        
        await cache.set("key1", "value1", tags=["tag1", "tag2"])
        await cache.set("key2", "value2", tags=["tag2", "tag3"])
        await cache.set("key3", "value3", tags=["tag4"])
        
        # Invalida por tag2
        removed = await cache.invalidate_by_tags(["tag2"])
        assert removed == 2
        
        # key1 e key2 devem ter sido removidas
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
        assert await cache.get("key3") == "value3"

    @pytest.mark.asyncio
    async def test_memory_cache_reset_stats(self):
        """Testa reset de estatísticas."""
        cache = MemoryCache()
        
        await cache.set("key1", "value1")
        await cache.get("key1")
        
        stats = await cache.get_stats()
        assert stats.hits == 1
        
        await cache.reset_stats()
        stats = await cache.get_stats()
        assert stats.hits == 0


class TestRedisCache:
    """Testes para cache Redis."""

    @pytest.fixture
    def mock_redis(self):
        """Mock do cliente Redis."""
        redis_mock = MagicMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.set = AsyncMock(return_value=True)
        redis_mock.delete = AsyncMock(return_value=1)
        redis_mock.exists = AsyncMock(return_value=False)
        redis_mock.flushdb = AsyncMock(return_value=True)
        redis_mock.keys = AsyncMock(return_value=[])
        redis_mock.ttl = AsyncMock(return_value=-1)
        redis_mock.ping = AsyncMock(return_value=True)
        return redis_mock

    @pytest.mark.asyncio
    async def test_redis_cache_init(self, mock_redis):
        """Testa inicialização do cache Redis."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            cache = RedisCache("redis://localhost:6379/0")
            await cache.connect()
            assert cache.redis is not None

    @pytest.mark.asyncio
    async def test_redis_cache_set_get(self, mock_redis):
        """Testa operações básicas de set/get."""
        mock_redis.get.return_value = b'"value1"'
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            cache = RedisCache("redis://localhost:6379/0")
            await cache.connect()
            
            await cache.set("key1", "value1")
            result = await cache.get("key1")
            
            assert result == "value1"
            mock_redis.set.assert_called()
            mock_redis.get.assert_called()

    @pytest.mark.asyncio
    async def test_redis_cache_get_nonexistent(self, mock_redis):
        """Testa get de chave inexistente."""
        mock_redis.get.return_value = None
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            cache = RedisCache("redis://localhost:6379/0")
            await cache.connect()
            
            result = await cache.get("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_redis_cache_delete(self, mock_redis):
        """Testa deleção de chave."""
        mock_redis.delete.return_value = 1
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            cache = RedisCache("redis://localhost:6379/0")
            await cache.connect()
            
            result = await cache.delete("key1")
            assert result is True
            mock_redis.delete.assert_called()

    @pytest.mark.asyncio
    async def test_redis_cache_clear(self, mock_redis):
        """Testa limpeza do cache."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            cache = RedisCache("redis://localhost:6379/0")
            await cache.connect()
            
            await cache.clear()
            mock_redis.flushdb.assert_called_once()


class TestCacheManager:
    """Testes para o gerenciador de cache."""

    @pytest.mark.asyncio
    async def test_cache_manager_memory_backend(self):
        """Testa CacheManager com backend de memória."""
        with patch('api.cache.settings') as mock_settings:
            mock_settings.CACHE_ENABLED = True
            mock_settings.REDIS_URL = None
            mock_settings.CACHE_MEMORY_SIZE = 1000
            mock_settings.CACHE_DEFAULT_TTL = 3600
            
            manager = CacheManager()
            await manager.initialize()
            
            assert isinstance(manager.backend, MemoryCache)

    @pytest.mark.asyncio
    async def test_cache_manager_redis_backend(self):
        """Testa CacheManager com backend Redis."""
        with patch('api.cache.settings') as mock_settings, \
             patch('redis.asyncio.from_url') as mock_redis:
            
            mock_settings.CACHE_ENABLED = True
            mock_settings.REDIS_URL = "redis://localhost:6379/0"
            mock_settings.CACHE_PREFIX = "pcs_cache:"
            
            mock_redis_client = MagicMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            mock_redis.return_value = mock_redis_client
            
            manager = CacheManager()
            await manager.initialize()
            
            assert isinstance(manager.backend, RedisCache)

    @pytest.mark.asyncio
    async def test_cache_manager_disabled(self):
        """Testa CacheManager quando cache está desabilitado."""
        with patch('api.cache.settings') as mock_settings:
            mock_settings.CACHE_ENABLED = False
            
            manager = CacheManager()
            await manager.initialize()
            
            # Operações devem retornar valores default
            result = await manager.get("key1")
            assert result is None
            
            result = await manager.set("key1", "value1")
            assert result is True

    @pytest.mark.asyncio
    async def test_cache_manager_operations(self):
        """Testa operações do CacheManager."""
        with patch('api.cache.settings') as mock_settings:
            mock_settings.CACHE_ENABLED = True
            mock_settings.REDIS_URL = None
            mock_settings.CACHE_MEMORY_SIZE = 1000
            mock_settings.CACHE_DEFAULT_TTL = 3600
            
            manager = CacheManager()
            await manager.initialize()
            
            # Set e Get
            await manager.set("test_key", "test_value")
            result = await manager.get("test_key")
            assert result == "test_value"
            
            # Delete
            result = await manager.delete("test_key")
            assert result is True
            
            result = await manager.get("test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_manager_stats(self):
        """Testa estatísticas do CacheManager."""
        with patch('api.cache.settings') as mock_settings:
            mock_settings.CACHE_ENABLED = True
            mock_settings.REDIS_URL = None
            mock_settings.CACHE_MEMORY_SIZE = 1000
            mock_settings.CACHE_DEFAULT_TTL = 3600
            
            manager = CacheManager()
            await manager.initialize()
            
            stats = await manager.get_stats()
            assert hasattr(stats, 'hits')
            assert hasattr(stats, 'misses')
            assert hasattr(stats, 'cache_size')
            assert hasattr(stats, 'memory_usage')