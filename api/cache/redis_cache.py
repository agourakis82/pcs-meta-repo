"""
Sistema H2 - Cache Redis

Implementação de cache Redis com conexão assíncrona.
"""

import asyncio
import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .manager import CacheBackendInterface, CacheConfig, CacheEntry


class RedisCache(CacheBackendInterface):
    """Cache Redis assíncrono."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client = None
        self.connected = False

        # Estatísticas
        self.stats_hits = 0
        self.stats_misses = 0
        self.stats_sets = 0
        self.stats_deletes = 0
        self.stats_errors = 0

        # Configurações Redis
        self.key_prefix = "pcs_cache:"
        self.metadata_prefix = "pcs_meta:"

    async def initialize(self):
        """Inicializa conexão Redis."""
        try:
            # Tentar importar redis
            try:
                import redis.asyncio as redis
            except ImportError:
                print("Warning: redis package not available, using mock Redis")
                self.redis_client = MockRedis()
                self.connected = True
                return

            # Configurar conexão
            if self.config.redis_url:
                self.redis_client = redis.from_url(
                    self.config.redis_url,
                    decode_responses=False,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                )
            else:
                self.redis_client = redis.Redis(
                    host="localhost",
                    port=6379,
                    decode_responses=False,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                )

            # Testar conexão
            await self.redis_client.ping()
            self.connected = True
            print("Redis cache initialized successfully")

        except Exception as e:
            print(f"Failed to initialize Redis: {e}")
            # Fallback para mock Redis
            self.redis_client = MockRedis()
            self.connected = True

    async def get(self, key: str) -> Optional[CacheEntry]:
        """Obtém item do cache Redis."""
        if not self.connected:
            return None

        try:
            redis_key = self._get_redis_key(key)
            meta_key = self._get_metadata_key(key)

            # Obter valor e metadados
            value_data = await self.redis_client.get(redis_key)
            meta_data = await self.redis_client.get(meta_key)

            if value_data is None:
                self.stats_misses += 1
                return None

            # Deserializar valor
            try:
                value = self._deserialize_value(value_data)
            except Exception as e:
                print(f"Error deserializing value for key {key}: {e}")
                self.stats_errors += 1
                return None

            # Processar metadados
            if meta_data:
                try:
                    metadata = json.loads(meta_data.decode())
                    entry = CacheEntry(
                        key=key,
                        value=value,
                        created_at=datetime.fromisoformat(metadata.get("created_at")),
                        expires_at=datetime.fromisoformat(metadata.get("expires_at"))
                        if metadata.get("expires_at")
                        else None,
                        access_count=metadata.get("access_count", 0) + 1,
                        last_accessed=datetime.now(),
                        size_bytes=metadata.get("size_bytes", 0),
                        compressed=metadata.get("compressed", False),
                        backend="redis",
                    )

                    # Atualizar metadados com novo acesso
                    await self._update_metadata(key, entry)

                except Exception as e:
                    print(f"Error processing metadata for key {key}: {e}")
                    # Criar entrada básica
                    entry = CacheEntry(
                        key=key,
                        value=value,
                        created_at=datetime.now(),
                        expires_at=None,
                        access_count=1,
                        last_accessed=datetime.now(),
                        size_bytes=len(str(value)),
                        backend="redis",
                    )
            else:
                # Criar entrada básica sem metadados
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=datetime.now(),
                    expires_at=None,
                    access_count=1,
                    last_accessed=datetime.now(),
                    size_bytes=len(str(value)),
                    backend="redis",
                )

            self.stats_hits += 1
            return entry

        except Exception as e:
            print(f"Error getting Redis key {key}: {e}")
            self.stats_errors += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Define item no cache Redis."""
        if not self.connected:
            return False

        try:
            redis_key = self._get_redis_key(key)
            meta_key = self._get_metadata_key(key)

            # Serializar valor
            try:
                serialized_value = self._serialize_value(value)
            except Exception as e:
                print(f"Error serializing value for key {key}: {e}")
                self.stats_errors += 1
                return False

            # Determinar TTL
            effective_ttl = ttl or self.config.default_ttl

            # Criar metadados
            metadata = {
                "created_at": datetime.now().isoformat(),
                "expires_at": (
                    datetime.now() + timedelta(seconds=effective_ttl)
                ).isoformat()
                if effective_ttl > 0
                else None,
                "access_count": 0,
                "size_bytes": len(serialized_value),
                "compressed": False,
            }

            # Armazenar valor e metadados
            pipe = self.redis_client.pipeline()

            if effective_ttl > 0:
                pipe.setex(redis_key, effective_ttl, serialized_value)
                pipe.setex(meta_key, effective_ttl, json.dumps(metadata))
            else:
                pipe.set(redis_key, serialized_value)
                pipe.set(meta_key, json.dumps(metadata))

            results = await pipe.execute()

            if all(results):
                self.stats_sets += 1
                return True
            else:
                self.stats_errors += 1
                return False

        except Exception as e:
            print(f"Error setting Redis key {key}: {e}")
            self.stats_errors += 1
            return False

    async def delete(self, key: str) -> bool:
        """Remove item do cache Redis."""
        if not self.connected:
            return False

        try:
            redis_key = self._get_redis_key(key)
            meta_key = self._get_metadata_key(key)

            # Deletar valor e metadados
            pipe = self.redis_client.pipeline()
            pipe.delete(redis_key)
            pipe.delete(meta_key)
            results = await pipe.execute()

            deleted_count = sum(results)
            if deleted_count > 0:
                self.stats_deletes += 1
                return True
            else:
                return False

        except Exception as e:
            print(f"Error deleting Redis key {key}: {e}")
            self.stats_errors += 1
            return False

    async def clear(self) -> bool:
        """Limpa todo o cache."""
        if not self.connected:
            return False

        try:
            # Buscar todas as chaves com prefixo
            pattern = f"{self.key_prefix}*"
            meta_pattern = f"{self.metadata_prefix}*"

            keys = await self.redis_client.keys(pattern)
            meta_keys = await self.redis_client.keys(meta_pattern)

            all_keys = keys + meta_keys

            if all_keys:
                deleted = await self.redis_client.delete(*all_keys)
                return deleted > 0
            else:
                return True

        except Exception as e:
            print(f"Error clearing Redis cache: {e}")
            self.stats_errors += 1
            return False

    async def exists(self, key: str) -> bool:
        """Verifica se chave existe."""
        if not self.connected:
            return False

        try:
            redis_key = self._get_redis_key(key)
            exists = await self.redis_client.exists(redis_key)
            return exists > 0
        except Exception as e:
            print(f"Error checking Redis key existence {key}: {e}")
            return False

    async def keys(self, pattern: str = "*") -> List[str]:
        """Lista chaves que correspondem ao padrão."""
        if not self.connected:
            return []

        try:
            # Converter padrão para Redis
            redis_pattern = f"{self.key_prefix}{pattern}"
            redis_keys = await self.redis_client.keys(redis_pattern)

            # Remover prefixo das chaves
            clean_keys = []
            for redis_key in redis_keys:
                if isinstance(redis_key, bytes):
                    redis_key = redis_key.decode()

                if redis_key.startswith(self.key_prefix):
                    clean_key = redis_key[len(self.key_prefix) :]
                    clean_keys.append(clean_key)

            return clean_keys

        except Exception as e:
            print(f"Error listing Redis keys: {e}")
            return []

    async def stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache Redis."""
        try:
            total_requests = self.stats_hits + self.stats_misses
            hit_rate = (self.stats_hits / total_requests) if total_requests > 0 else 0

            # Estatísticas básicas
            basic_stats = {
                "backend": "redis",
                "connected": self.connected,
                "hits": self.stats_hits,
                "misses": self.stats_misses,
                "hit_rate": hit_rate,
                "sets": self.stats_sets,
                "deletes": self.stats_deletes,
                "errors": self.stats_errors,
            }

            # Tentar obter estatísticas do Redis
            if self.connected:
                try:
                    redis_info = await self.redis_client.info("memory")
                    basic_stats.update(
                        {
                            "redis_memory_used": redis_info.get("used_memory", 0),
                            "redis_memory_human": redis_info.get(
                                "used_memory_human", "Unknown"
                            ),
                            "redis_connections": redis_info.get("connected_clients", 0),
                        }
                    )
                except Exception:
                    pass  # Ignorar erros de estatísticas Redis

            return basic_stats

        except Exception as e:
            print(f"Error getting Redis stats: {e}")
            return {"backend": "redis", "error": str(e)}

    def _get_redis_key(self, key: str) -> str:
        """Gera chave Redis com prefixo."""
        return f"{self.key_prefix}{key}"

    def _get_metadata_key(self, key: str) -> str:
        """Gera chave de metadados Redis."""
        return f"{self.metadata_prefix}{key}"

    def _serialize_value(self, value: Any) -> bytes:
        """Serializa valor para armazenamento."""
        try:
            if isinstance(value, (str, int, float, bool)):
                return json.dumps(value).encode()
            else:
                return pickle.dumps(value)
        except Exception:
            # Fallback para string
            return str(value).encode()

    def _deserialize_value(self, data: bytes) -> Any:
        """Deserializa valor do armazenamento."""
        try:
            # Tentar JSON primeiro
            return json.loads(data.decode())
        except Exception:
            try:
                # Tentar pickle
                return pickle.loads(data)
            except Exception:
                # Fallback para string
                return data.decode()

    async def _update_metadata(self, key: str, entry: CacheEntry):
        """Atualiza metadados da entrada."""
        try:
            meta_key = self._get_metadata_key(key)

            metadata = {
                "created_at": entry.created_at.isoformat(),
                "expires_at": entry.expires_at.isoformat()
                if entry.expires_at
                else None,
                "access_count": entry.access_count,
                "last_accessed": entry.last_accessed.isoformat()
                if entry.last_accessed
                else None,
                "size_bytes": entry.size_bytes,
                "compressed": entry.compressed,
            }

            # Obter TTL restante
            redis_key = self._get_redis_key(key)
            ttl = await self.redis_client.ttl(redis_key)

            if ttl > 0:
                await self.redis_client.setex(meta_key, ttl, json.dumps(metadata))
            else:
                await self.redis_client.set(meta_key, json.dumps(metadata))

        except Exception as e:
            print(f"Error updating metadata for key {key}: {e}")

    async def shutdown(self):
        """Finaliza conexão Redis."""
        if self.redis_client and hasattr(self.redis_client, "close"):
            try:
                await self.redis_client.close()
            except Exception:
                pass

        self.connected = False
        print("Redis cache shutdown complete")


class MockRedis:
    """Mock Redis para testes/fallback."""

    def __init__(self):
        self.data: Dict[str, bytes] = {}
        self.expires: Dict[str, datetime] = {}

    async def ping(self):
        """Mock ping."""
        return True

    async def get(self, key: str) -> Optional[bytes]:
        """Mock get."""
        if key in self.expires and datetime.now() > self.expires[key]:
            del self.data[key]
            del self.expires[key]
            return None

        return self.data.get(key)

    async def set(self, key: str, value: bytes) -> bool:
        """Mock set."""
        self.data[key] = value
        return True

    async def setex(self, key: str, ttl: int, value: bytes) -> bool:
        """Mock setex."""
        self.data[key] = value
        self.expires[key] = datetime.now() + timedelta(seconds=ttl)
        return True

    async def delete(self, *keys: str) -> int:
        """Mock delete."""
        count = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                count += 1
            if key in self.expires:
                del self.expires[key]
        return count

    async def exists(self, key: str) -> int:
        """Mock exists."""
        if key in self.expires and datetime.now() > self.expires[key]:
            del self.data[key]
            del self.expires[key]
            return 0

        return 1 if key in self.data else 0

    async def keys(self, pattern: str) -> List[bytes]:
        """Mock keys."""
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [key.encode() for key in self.data.keys() if key.startswith(prefix)]
        else:
            return [pattern.encode()] if pattern in self.data else []

    async def ttl(self, key: str) -> int:
        """Mock TTL."""
        if key in self.expires:
            remaining = self.expires[key] - datetime.now()
            return max(0, int(remaining.total_seconds()))
        return -1

    async def info(self, section: str = "default") -> Dict[str, Any]:
        """Mock info."""
        return {
            "used_memory": len(str(self.data)),
            "used_memory_human": f"{len(str(self.data))}B",
            "connected_clients": 1,
        }

    def pipeline(self):
        """Mock pipeline."""
        return MockPipeline(self)

    async def close(self):
        """Mock close."""
        pass


class MockPipeline:
    """Mock Redis pipeline."""

    def __init__(self, redis_mock: MockRedis):
        self.redis = redis_mock
        self.commands = []

    def set(self, key: str, value: bytes):
        """Mock pipeline set."""
        self.commands.append(("set", key, value))
        return self

    def setex(self, key: str, ttl: int, value: bytes):
        """Mock pipeline setex."""
        self.commands.append(("setex", key, ttl, value))
        return self

    def delete(self, key: str):
        """Mock pipeline delete."""
        self.commands.append(("delete", key))
        return self

    async def execute(self) -> List[bool]:
        """Mock pipeline execute."""
        results = []
        for cmd in self.commands:
            if cmd[0] == "set":
                result = await self.redis.set(cmd[1], cmd[2])
            elif cmd[0] == "setex":
                result = await self.redis.setex(cmd[1], cmd[2], cmd[3])
            elif cmd[0] == "delete":
                result = await self.redis.delete(cmd[1])
            else:
                result = True

            results.append(result)

        self.commands.clear()
        return results
