"""
Sistema de Cache e Performance para PCS-HELIO MCP Server.

Implementa múltiplas camadas de cache com suporte a Redis e memória local,
decorators para cache automático, warming de cache e métricas de performance.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from pydantic import BaseModel, Field

from ..config import settings
from ..logging import get_logger

logger = get_logger("cache")


@dataclass
class CacheStats:
    """Estatísticas de performance do cache."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    total_time_saved: float = 0.0
    average_hit_time: float = 0.0
    average_miss_time: float = 0.0
    cache_size: int = 0
    memory_usage: int = 0
    last_reset: datetime = field(default_factory=datetime.now)
    
    @property
    def hit_rate(self) -> float:
        """Taxa de hits do cache."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    @property
    def miss_rate(self) -> float:
        """Taxa de misses do cache."""
        return 1.0 - self.hit_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate, 4),
            "miss_rate": round(self.miss_rate, 4),
            "total_time_saved_ms": round(self.total_time_saved * 1000, 2),
            "average_hit_time_ms": round(self.average_hit_time * 1000, 2),
            "average_miss_time_ms": round(self.average_miss_time * 1000, 2),
            "cache_size": self.cache_size,
            "memory_usage_bytes": self.memory_usage,
            "last_reset": self.last_reset.isoformat()
        }


class CacheEntry(BaseModel):
    """Entrada do cache com metadata."""
    value: Any = Field(..., description="Valor cached")
    created_at: datetime = Field(..., description="Timestamp de criação")
    expires_at: Optional[datetime] = Field(None, description="Timestamp de expiração")
    access_count: int = Field(default=0, description="Número de acessos")
    last_accessed: datetime = Field(..., description="Último acesso")
    size_bytes: int = Field(default=0, description="Tamanho em bytes")
    tags: List[str] = Field(default_factory=list, description="Tags para invalidação")
    
    @property
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def age_seconds(self) -> float:
        """Idade da entrada em segundos."""
        return (datetime.now() - self.created_at).total_seconds()
    
    def update_access(self) -> None:
        """Atualiza estatísticas de acesso."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class MemoryCache:
    """Cache em memória com LRU e TTL."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache."""
        async with self._lock:
            start_time = time.time()
            
            self._stats.total_requests += 1
            
            if key not in self._cache:
                self._stats.misses += 1
                self._stats.average_miss_time = self._update_average(
                    self._stats.average_miss_time, time.time() - start_time, self._stats.misses
                )
                logger.debug(f"Cache miss: {key}")
                return None
            
            entry = self._cache[key]
            
            # Verifica expiração
            if entry.is_expired:
                await self._remove(key)
                self._stats.misses += 1
                self._stats.average_miss_time = self._update_average(
                    self._stats.average_miss_time, time.time() - start_time, self._stats.misses
                )
                logger.debug(f"Cache miss (expired): {key}")
                return None
            
            # Hit - atualiza estatísticas
            entry.update_access()
            self._update_access_order(key)
            
            self._stats.hits += 1
            hit_time = time.time() - start_time
            self._stats.average_hit_time = self._update_average(
                self._stats.average_hit_time, hit_time, self._stats.hits
            )
            
            logger.debug(f"Cache hit: {key} (age: {entry.age_seconds:.1f}s)")
            return entry.value
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """Define valor no cache."""
        async with self._lock:
            ttl = ttl or self.default_ttl
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
            
            # Estima tamanho
            size_bytes = len(str(value).encode('utf-8'))
            
            entry = CacheEntry(
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at,
                last_accessed=datetime.now(),
                size_bytes=size_bytes,
                tags=tags or []
            )
            
            # Remove entrada existente se houver
            if key in self._cache:
                await self._remove(key)
            
            # Verifica se precisa fazer eviction
            await self._ensure_capacity()
            
            self._cache[key] = entry
            self._access_order.append(key)
            
            logger.debug(f"Cache set: {key} (ttl: {ttl}s, size: {size_bytes}B)")
    
    async def delete(self, key: str) -> bool:
        """Remove chave do cache."""
        async with self._lock:
            if key in self._cache:
                await self._remove(key)
                logger.debug(f"Cache delete: {key}")
                return True
            return False
    
    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalida entradas por tags."""
        async with self._lock:
            keys_to_remove = []
            
            for key, entry in self._cache.items():
                if any(tag in entry.tags for tag in tags):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                await self._remove(key)
            
            logger.info(f"Cache invalidation: {len(keys_to_remove)} entries removed for tags {tags}")
            return len(keys_to_remove)
    
    async def clear(self) -> None:
        """Limpa todo o cache."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            logger.info("Cache cleared")
    
    async def get_stats(self) -> CacheStats:
        """Obtém estatísticas do cache."""
        async with self._lock:
            self._stats.cache_size = len(self._cache)
            self._stats.memory_usage = sum(entry.size_bytes for entry in self._cache.values())
            return self._stats
    
    async def reset_stats(self) -> None:
        """Reseta estatísticas."""
        async with self._lock:
            self._stats = CacheStats()
            logger.info("Cache stats reset")
    
    async def _remove(self, key: str) -> None:
        """Remove entrada do cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)
    
    def _update_access_order(self, key: str) -> None:
        """Atualiza ordem de acesso para LRU."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    async def _ensure_capacity(self) -> None:
        """Garante que há espaço no cache."""
        while len(self._cache) >= self.max_size and self._access_order:
            # Remove item mais antigo (LRU)
            oldest_key = self._access_order[0]
            await self._remove(oldest_key)
            self._stats.evictions += 1
            logger.debug(f"Cache eviction (LRU): {oldest_key}")
    
    def _update_average(self, current_avg: float, new_value: float, count: int) -> float:
        """Atualiza média incremental."""
        if count == 1:
            return new_value
        return ((current_avg * (count - 1)) + new_value) / count


class RedisCache:
    """Cache Redis com features avançadas."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "pcs_cache:"):
        self.redis_url = redis_url
        self.prefix = prefix
        self._redis: Optional[redis.Redis] = None
        self._stats = CacheStats()
        
    async def connect(self) -> None:
        """Conecta ao Redis."""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis library not available")
        
        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info(f"Connected to Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Desconecta do Redis."""
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis")
    
    def _make_key(self, key: str) -> str:
        """Cria chave completa com prefix."""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtém valor do Redis."""
        if not self._redis:
            raise RuntimeError("Redis not connected")
        
        start_time = time.time()
        self._stats.total_requests += 1
        
        try:
            redis_key = self._make_key(key)
            raw_data = await self._redis.get(redis_key)
            
            if raw_data is None:
                self._stats.misses += 1
                return None
            
            # Deserializa dados
            data = json.loads(raw_data)
            entry_data = data.get('entry', {})
            
            # Verifica expiração manual (Redis TTL é backup)
            if 'expires_at' in entry_data and entry_data['expires_at']:
                expires_at = datetime.fromisoformat(entry_data['expires_at'])
                if datetime.now() > expires_at:
                    await self.delete(key)
                    self._stats.misses += 1
                    return None
            
            # Hit
            self._stats.hits += 1
            hit_time = time.time() - start_time
            self._stats.average_hit_time = self._update_average(
                self._stats.average_hit_time, hit_time, self._stats.hits
            )
            
            # Atualiza contador de acesso
            entry_data['access_count'] = entry_data.get('access_count', 0) + 1
            entry_data['last_accessed'] = datetime.now().isoformat()
            
            # Salva dados atualizados
            updated_data = {'entry': entry_data, 'value': data['value']}
            await self._redis.set(redis_key, json.dumps(updated_data), keepttl=True)
            
            logger.debug(f"Redis cache hit: {key}")
            return data['value']
            
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self._stats.misses += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """Define valor no Redis."""
        if not self._redis:
            raise RuntimeError("Redis not connected")
        
        try:
            redis_key = self._make_key(key)
            
            # Prepara entrada
            expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat() if ttl else None
            
            entry_data = {
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at,
                'access_count': 0,
                'last_accessed': datetime.now().isoformat(),
                'tags': tags or []
            }
            
            data = {
                'entry': entry_data,
                'value': value
            }
            
            # Salva no Redis
            await self._redis.set(redis_key, json.dumps(data), ex=ttl)
            
            # Adiciona tags para invalidação
            if tags:
                for tag in tags:
                    tag_key = f"{self.prefix}tag:{tag}"
                    await self._redis.sadd(tag_key, key)
                    if ttl:
                        await self._redis.expire(tag_key, ttl + 3600)  # TTL + buffer
            
            logger.debug(f"Redis cache set: {key} (ttl: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    async def delete(self, key: str) -> bool:
        """Remove chave do Redis."""
        if not self._redis:
            raise RuntimeError("Redis not connected")
        
        try:
            redis_key = self._make_key(key)
            result = await self._redis.delete(redis_key)
            if result > 0:
                logger.debug(f"Redis cache delete: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalida entradas por tags."""
        if not self._redis:
            raise RuntimeError("Redis not connected")
        
        try:
            total_removed = 0
            
            for tag in tags:
                tag_key = f"{self.prefix}tag:{tag}"
                
                # Obtém todas as chaves com esta tag
                keys = await self._redis.smembers(tag_key)
                
                if keys:
                    # Remove chaves de cache
                    redis_keys = [self._make_key(key) for key in keys]
                    removed = await self._redis.delete(*redis_keys)
                    total_removed += removed
                    
                    # Remove a tag
                    await self._redis.delete(tag_key)
            
            logger.info(f"Redis invalidation: {total_removed} entries removed for tags {tags}")
            return total_removed
            
        except Exception as e:
            logger.error(f"Redis invalidation error: {e}")
            return 0
    
    async def clear(self) -> None:
        """Limpa cache Redis (apenas com prefix)."""
        if not self._redis:
            raise RuntimeError("Redis not connected")
        
        try:
            # Busca todas as chaves com o prefix
            pattern = f"{self.prefix}*"
            keys = []
            
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self._redis.delete(*keys)
                logger.info(f"Redis cache cleared: {len(keys)} keys removed")
            
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
    
    async def get_stats(self) -> CacheStats:
        """Obtém estatísticas do Redis cache."""
        if not self._redis:
            raise RuntimeError("Redis not connected")
        
        try:
            # Conta chaves com nosso prefix
            pattern = f"{self.prefix}*"
            count = 0
            memory_usage = 0
            
            async for key in self._redis.scan_iter(match=pattern):
                count += 1
                try:
                    memory_usage += await self._redis.memory_usage(key) or 0
                except Exception:
                    pass  # memory_usage pode não estar disponível
            
            self._stats.cache_size = count
            self._stats.memory_usage = memory_usage
            
            return self._stats
            
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return self._stats
    
    def _update_average(self, current_avg: float, new_value: float, count: int) -> float:
        """Atualiza média incremental."""
        if count == 1:
            return new_value
        return ((current_avg * (count - 1)) + new_value) / count


class CacheManager:
    """Gerenciador unificado de cache com múltiplas camadas."""
    
    def __init__(self):
        self.memory_cache = MemoryCache(
            max_size=getattr(settings, 'CACHE_MEMORY_SIZE', 1000),
            default_ttl=getattr(settings, 'CACHE_DEFAULT_TTL', 3600)
        )
        
        self.redis_cache: Optional[RedisCache] = None
        
        # Configuração Redis
        redis_url = getattr(settings, 'REDIS_URL', None)
        if redis_url and REDIS_AVAILABLE:
            self.redis_cache = RedisCache(
                redis_url=redis_url,
                prefix=getattr(settings, 'CACHE_PREFIX', 'pcs_cache:')
            )
    
    async def initialize(self) -> None:
        """Inicializa o cache manager."""
        if self.redis_cache:
            try:
                await self.redis_cache.connect()
                logger.info("Cache manager initialized with Redis")
            except Exception as e:
                logger.warning(f"Redis unavailable, using memory cache only: {e}")
                self.redis_cache = None
        else:
            logger.info("Cache manager initialized with memory cache only")
    
    async def shutdown(self) -> None:
        """Finaliza o cache manager."""
        if self.redis_cache:
            await self.redis_cache.disconnect()
        logger.info("Cache manager shutdown")
    
    async def get(self, key: str, use_redis: bool = True) -> Optional[Any]:
        """Obtém valor do cache (L1: memory, L2: Redis)."""
        # Tenta memory cache primeiro (L1)
        value = await self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Tenta Redis cache (L2)
        if use_redis and self.redis_cache:
            value = await self.redis_cache.get(key)
            if value is not None:
                # Popula memory cache
                await self.memory_cache.set(key, value, ttl=300)  # 5 min no L1
                return value
        
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        use_redis: bool = True
    ) -> None:
        """Define valor no cache."""
        # Define no memory cache (L1)
        memory_ttl = min(ttl or 3600, 300)  # Max 5 min no memory
        await self.memory_cache.set(key, value, ttl=memory_ttl, tags=tags)
        
        # Define no Redis cache (L2)
        if use_redis and self.redis_cache:
            await self.redis_cache.set(key, value, ttl=ttl, tags=tags)
    
    async def delete(self, key: str) -> bool:
        """Remove chave de ambos os caches."""
        memory_result = await self.memory_cache.delete(key)
        redis_result = False
        
        if self.redis_cache:
            redis_result = await self.redis_cache.delete(key)
        
        return memory_result or redis_result
    
    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalida entradas por tags em ambos os caches."""
        memory_count = await self.memory_cache.invalidate_by_tags(tags)
        redis_count = 0
        
        if self.redis_cache:
            redis_count = await self.redis_cache.invalidate_by_tags(tags)
        
        return memory_count + redis_count
    
    async def clear(self) -> None:
        """Limpa ambos os caches."""
        await self.memory_cache.clear()
        
        if self.redis_cache:
            await self.redis_cache.clear()
    
    async def get_combined_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas combinadas."""
        memory_stats = await self.memory_cache.get_stats()
        redis_stats = None
        
        if self.redis_cache:
            redis_stats = await self.redis_cache.get_stats()
        
        return {
            "memory_cache": memory_stats.to_dict(),
            "redis_cache": redis_stats.to_dict() if redis_stats else None,
            "redis_available": self.redis_cache is not None
        }


# Instância global do cache manager
cache_manager = CacheManager()


def cache_key(*args, **kwargs) -> str:
    """Gera chave de cache determinística."""
    # Combina argumentos em string estável
    key_parts = []
    
    # Adiciona args
    for arg in args:
        if hasattr(arg, '__dict__'):
            key_parts.append(str(sorted(arg.__dict__.items())))
        else:
            key_parts.append(str(arg))
    
    # Adiciona kwargs ordenados
    if kwargs:
        key_parts.append(str(sorted(kwargs.items())))
    
    # Gera hash MD5
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    ttl: int = 3600,
    key_generator: Optional[Callable] = None,
    tags: Optional[List[str]] = None,
    use_redis: bool = True
):
    """
    Decorator para cache automático de funções.
    
    Args:
        ttl: Time to live em segundos
        key_generator: Função customizada para gerar chave
        tags: Tags para invalidação
        use_redis: Se deve usar Redis
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Gera chave de cache
            if key_generator:
                key = key_generator(*args, **kwargs)
            else:
                func_name = f"{func.__module__}.{func.__name__}"
                arg_key = cache_key(*args, **kwargs)
                key = f"{func_name}:{arg_key}"
            
            # Tenta obter do cache
            cached_value = await cache_manager.get(key, use_redis=use_redis)
            if cached_value is not None:
                logger.debug(f"Cache hit for function: {func.__name__}")
                return cached_value
            
            # Executa função
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Salva no cache
            await cache_manager.set(key, result, ttl=ttl, tags=tags, use_redis=use_redis)
            
            logger.debug(f"Function cached: {func.__name__} (exec_time: {execution_time:.3f}s)")
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Para funções síncronas, executa em loop de eventos
            import asyncio
            
            async def async_version():
                return await async_wrapper(*args, **kwargs)
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Se já estamos em um loop, executa em thread pool
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(lambda: asyncio.run(async_version()))
                        return future.result()
                else:
                    return loop.run_until_complete(async_version())
            except Exception:
                return asyncio.run(async_version())
        
        # Retorna wrapper apropriado
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CacheWarmer:
    """Sistema de aquecimento de cache."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.warming_tasks: Dict[str, asyncio.Task] = {}
        self.logger = get_logger("cache_warmer")
    
    async def warm_cache(
        self,
        name: str,
        func: Callable,
        schedule_interval: int = 3600,
        *args,
        **kwargs
    ) -> None:
        """
        Agenda aquecimento periódico do cache.
        
        Args:
            name: Nome único para o warming task
            func: Função a ser executada
            schedule_interval: Intervalo em segundos
            *args, **kwargs: Argumentos para a função
        """
        async def warming_loop():
            while True:
                try:
                    start_time = time.time()
                    
                    if asyncio.iscoroutinefunction(func):
                        await func(*args, **kwargs)
                    else:
                        func(*args, **kwargs)
                    
                    execution_time = time.time() - start_time
                    self.logger.info(
                        f"Cache warmed: {name} (execution_time: {execution_time:.3f}s)"
                    )
                    
                except Exception as e:
                    self.logger.error(f"Cache warming error for {name}: {e}")
                
                await asyncio.sleep(schedule_interval)
        
        # Cancela task anterior se existir
        if name in self.warming_tasks:
            self.warming_tasks[name].cancel()
        
        # Inicia nova task
        self.warming_tasks[name] = asyncio.create_task(warming_loop())
        self.logger.info(f"Cache warming scheduled: {name} (interval: {schedule_interval}s)")
    
    async def stop_warming(self, name: str) -> None:
        """Para o aquecimento de cache."""
        if name in self.warming_tasks:
            self.warming_tasks[name].cancel()
            del self.warming_tasks[name]
            self.logger.info(f"Cache warming stopped: {name}")
    
    async def stop_all_warming(self) -> None:
        """Para todos os aquecimentos."""
        for name in list(self.warming_tasks.keys()):
            await self.stop_warming(name)


# Instância global do cache warmer
cache_warmer = CacheWarmer(cache_manager)


# Funções de conveniência
async def get_cache_stats() -> Dict[str, Any]:
    """Obtém estatísticas completas do cache."""
    return await cache_manager.get_combined_stats()


async def invalidate_cache_tags(tags: List[str]) -> int:
    """Invalida cache por tags."""
    return await cache_manager.invalidate_by_tags(tags)


async def clear_all_cache() -> None:
    """Limpa todo o cache."""
    await cache_manager.clear()
