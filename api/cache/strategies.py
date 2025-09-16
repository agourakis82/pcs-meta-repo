"""
Sistema H2 - Estratégias de Invalidação de Cache

Módulo para diferentes estratégias de invalidação e limpeza de cache.
"""

import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class InvalidationStrategy(ABC):
    """Interface para estratégias de invalidação."""

    @abstractmethod
    async def should_invalidate(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Determina se uma chave deve ser invalidada."""
        pass

    @abstractmethod
    async def on_access(self, key: str, metadata: Dict[str, Any]):
        """Callback quando uma chave é acessada."""
        pass

    @abstractmethod
    async def on_set(self, key: str, metadata: Dict[str, Any]):
        """Callback quando uma chave é definida."""
        pass

    @abstractmethod
    async def cleanup(self) -> Set[str]:
        """Retorna conjunto de chaves para invalidar."""
        pass


class TTLStrategy(InvalidationStrategy):
    """Estratégia de invalidação baseada em TTL (Time To Live)."""

    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self.expiry_times: Dict[str, float] = {}
        self.lock = threading.RLock()

    async def should_invalidate(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Verifica se chave expirou."""
        with self.lock:
            if key not in self.expiry_times:
                return False

            return time.time() > self.expiry_times[key]

    async def on_access(self, key: str, metadata: Dict[str, Any]):
        """Atualiza último acesso (não usado em TTL básico)."""
        pass

    async def on_set(self, key: str, metadata: Dict[str, Any]):
        """Define tempo de expiração."""
        with self.lock:
            ttl = metadata.get("ttl", self.default_ttl)
            self.expiry_times[key] = time.time() + ttl

    async def cleanup(self) -> Set[str]:
        """Retorna chaves expiradas."""
        with self.lock:
            current_time = time.time()
            expired_keys = {
                key
                for key, expiry in self.expiry_times.items()
                if current_time > expiry
            }

            # Remove da tracking
            for key in expired_keys:
                del self.expiry_times[key]

            return expired_keys


class LRUStrategy(InvalidationStrategy):
    """Estratégia LRU (Least Recently Used)."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}
        self.access_order: List[str] = []
        self.lock = threading.RLock()

    async def should_invalidate(self, key: str, metadata: Dict[str, Any]) -> bool:
        """LRU não invalida individual - só no cleanup."""
        return False

    async def on_access(self, key: str, metadata: Dict[str, Any]):
        """Atualiza ordem de acesso."""
        with self.lock:
            current_time = time.time()
            self.access_times[key] = current_time

            # Atualizar ordem
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

    async def on_set(self, key: str, metadata: Dict[str, Any]):
        """Registra nova chave."""
        await self.on_access(key, metadata)

    async def cleanup(self) -> Set[str]:
        """Remove chaves menos usadas se exceder limite."""
        with self.lock:
            if len(self.access_order) <= self.max_size:
                return set()

            # Remover as mais antigas
            excess = len(self.access_order) - self.max_size
            to_remove = set(self.access_order[:excess])

            # Atualizar estruturas
            for key in to_remove:
                if key in self.access_times:
                    del self.access_times[key]

            self.access_order = self.access_order[excess:]

            return to_remove


class LFUStrategy(InvalidationStrategy):
    """Estratégia LFU (Least Frequently Used)."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.lock = threading.RLock()

    async def should_invalidate(self, key: str, metadata: Dict[str, Any]) -> bool:
        """LFU não invalida individual - só no cleanup."""
        return False

    async def on_access(self, key: str, metadata: Dict[str, Any]):
        """Incrementa contador de acesso."""
        with self.lock:
            self.access_counts[key] += 1

    async def on_set(self, key: str, metadata: Dict[str, Any]):
        """Inicializa contador."""
        with self.lock:
            if key not in self.access_counts:
                self.access_counts[key] = 1
            else:
                self.access_counts[key] += 1

    async def cleanup(self) -> Set[str]:
        """Remove chaves menos frequentemente usadas."""
        with self.lock:
            if len(self.access_counts) <= self.max_size:
                return set()

            # Ordenar por frequência
            sorted_keys = sorted(self.access_counts.items(), key=lambda x: x[1])

            # Remover as menos frequentes
            excess = len(self.access_counts) - self.max_size
            to_remove = set(key for key, _ in sorted_keys[:excess])

            # Atualizar contadores
            for key in to_remove:
                del self.access_counts[key]

            return to_remove


class TagStrategy(InvalidationStrategy):
    """Estratégia baseada em tags/grupos."""

    def __init__(self):
        self.key_tags: Dict[str, Set[str]] = defaultdict(set)
        self.tag_keys: Dict[str, Set[str]] = defaultdict(set)
        self.invalidated_tags: Set[str] = set()
        self.lock = threading.RLock()

    async def should_invalidate(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Verifica se alguma tag da chave foi invalidada."""
        with self.lock:
            if key not in self.key_tags:
                return False

            return bool(self.key_tags[key] & self.invalidated_tags)

    async def on_access(self, key: str, metadata: Dict[str, Any]):
        """Não faz nada no acesso."""
        pass

    async def on_set(self, key: str, metadata: Dict[str, Any]):
        """Registra tags da chave."""
        tags = metadata.get("tags", [])
        if not tags:
            return

        with self.lock:
            # Limpar tags antigas
            old_tags = self.key_tags.get(key, set())
            for tag in old_tags:
                self.tag_keys[tag].discard(key)

            # Registrar novas tags
            self.key_tags[key] = set(tags)
            for tag in tags:
                self.tag_keys[tag].add(key)

    async def invalidate_tag(self, tag: str):
        """Invalida todas as chaves com uma tag."""
        with self.lock:
            self.invalidated_tags.add(tag)

    async def cleanup(self) -> Set[str]:
        """Retorna chaves com tags invalidadas."""
        with self.lock:
            if not self.invalidated_tags:
                return set()

            to_remove = set()
            for tag in self.invalidated_tags:
                if tag in self.tag_keys:
                    to_remove.update(self.tag_keys[tag])

            # Limpar tags invalidadas
            for tag in self.invalidated_tags:
                if tag in self.tag_keys:
                    for key in self.tag_keys[tag]:
                        self.key_tags[key].discard(tag)
                    del self.tag_keys[tag]

            self.invalidated_tags.clear()

            return to_remove


class DependencyStrategy(InvalidationStrategy):
    """Estratégia baseada em dependências entre chaves."""

    def __init__(self):
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.dependents: Dict[str, Set[str]] = defaultdict(set)
        self.invalidated_keys: Set[str] = set()
        self.lock = threading.RLock()

    async def should_invalidate(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Verifica se chave ou suas dependências foram invalidadas."""
        with self.lock:
            return key in self.invalidated_keys

    async def on_access(self, key: str, metadata: Dict[str, Any]):
        """Não faz nada no acesso."""
        pass

    async def on_set(self, key: str, metadata: Dict[str, Any]):
        """Registra dependências da chave."""
        deps = metadata.get("dependencies", [])
        if not deps:
            return

        with self.lock:
            # Limpar dependências antigas
            old_deps = self.dependencies.get(key, set())
            for dep in old_deps:
                self.dependents[dep].discard(key)

            # Registrar novas dependências
            self.dependencies[key] = set(deps)
            for dep in deps:
                self.dependents[dep].add(key)

    async def invalidate_key(self, key: str):
        """Invalida chave e todos os seus dependentes."""
        with self.lock:
            to_invalidate = {key}
            stack = [key]

            while stack:
                current = stack.pop()
                if current in self.dependents:
                    for dependent in self.dependents[current]:
                        if dependent not in to_invalidate:
                            to_invalidate.add(dependent)
                            stack.append(dependent)

            self.invalidated_keys.update(to_invalidate)

    async def cleanup(self) -> Set[str]:
        """Retorna chaves invalidadas."""
        with self.lock:
            to_remove = self.invalidated_keys.copy()

            # Limpar dependências das chaves removidas
            for key in to_remove:
                if key in self.dependencies:
                    for dep in self.dependencies[key]:
                        self.dependents[dep].discard(key)
                    del self.dependencies[key]

                if key in self.dependents:
                    del self.dependents[key]

            self.invalidated_keys.clear()

            return to_remove


class ConditionalStrategy(InvalidationStrategy):
    """Estratégia baseada em condições customizadas."""

    def __init__(self, condition_func: Callable[[str, Dict[str, Any]], bool]):
        self.condition_func = condition_func
        self.keys_metadata: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()

    async def should_invalidate(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Avalia condição customizada."""
        try:
            return self.condition_func(key, metadata)
        except Exception as e:
            logger.error(f"Error in conditional strategy: {e}")
            return False

    async def on_access(self, key: str, metadata: Dict[str, Any]):
        """Atualiza último acesso."""
        with self.lock:
            if key not in self.keys_metadata:
                self.keys_metadata[key] = {}
            self.keys_metadata[key]["last_access"] = time.time()

    async def on_set(self, key: str, metadata: Dict[str, Any]):
        """Registra metadados."""
        with self.lock:
            self.keys_metadata[key] = metadata.copy()
            self.keys_metadata[key]["created_at"] = time.time()

    async def cleanup(self) -> Set[str]:
        """Avalia condição para todas as chaves."""
        with self.lock:
            to_remove = set()

            for key, metadata in self.keys_metadata.items():
                try:
                    if self.condition_func(key, metadata):
                        to_remove.add(key)
                except Exception as e:
                    logger.error(f"Error evaluating condition for {key}: {e}")

            # Remove metadados das chaves invalidadas
            for key in to_remove:
                del self.keys_metadata[key]

            return to_remove


class CompositeStrategy(InvalidationStrategy):
    """Composição de múltiplas estratégias."""

    def __init__(self, strategies: List[InvalidationStrategy]):
        self.strategies = strategies

    async def should_invalidate(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Chave é invalidada se qualquer estratégia disser para invalidar."""
        for strategy in self.strategies:
            if await strategy.should_invalidate(key, metadata):
                return True
        return False

    async def on_access(self, key: str, metadata: Dict[str, Any]):
        """Notifica todas as estratégias."""
        for strategy in self.strategies:
            await strategy.on_access(key, metadata)

    async def on_set(self, key: str, metadata: Dict[str, Any]):
        """Notifica todas as estratégias."""
        for strategy in self.strategies:
            await strategy.on_set(key, metadata)

    async def cleanup(self) -> Set[str]:
        """Coleta chaves de todas as estratégias."""
        all_keys = set()
        for strategy in self.strategies:
            keys = await strategy.cleanup()
            all_keys.update(keys)
        return all_keys


class InvalidationManager:
    """Gerenciador de estratégias de invalidação."""

    def __init__(self):
        self.strategies: Dict[str, InvalidationStrategy] = {}
        self.active_strategy: Optional[str] = None
        self.lock = threading.RLock()

    def register_strategy(self, name: str, strategy: InvalidationStrategy):
        """Registra uma estratégia."""
        with self.lock:
            self.strategies[name] = strategy

    def set_active_strategy(self, name: str):
        """Define estratégia ativa."""
        with self.lock:
            if name not in self.strategies:
                raise ValueError(f"Strategy '{name}' not registered")
            self.active_strategy = name

    def get_active_strategy(self) -> Optional[InvalidationStrategy]:
        """Obtém estratégia ativa."""
        with self.lock:
            if self.active_strategy:
                return self.strategies.get(self.active_strategy)
            return None

    async def should_invalidate(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Verifica se chave deve ser invalidada."""
        strategy = self.get_active_strategy()
        if strategy:
            return await strategy.should_invalidate(key, metadata)
        return False

    async def on_access(self, key: str, metadata: Dict[str, Any]):
        """Notifica acesso à chave."""
        strategy = self.get_active_strategy()
        if strategy:
            await strategy.on_access(key, metadata)

    async def on_set(self, key: str, metadata: Dict[str, Any]):
        """Notifica definição de chave."""
        strategy = self.get_active_strategy()
        if strategy:
            await strategy.on_set(key, metadata)

    async def cleanup(self) -> Set[str]:
        """Executa limpeza da estratégia ativa."""
        strategy = self.get_active_strategy()
        if strategy:
            return await strategy.cleanup()
        return set()


def create_default_strategies() -> Dict[str, InvalidationStrategy]:
    """Cria estratégias padrão."""
    return {
        "ttl": TTLStrategy(default_ttl=3600),
        "lru": LRUStrategy(max_size=1000),
        "lfu": LFUStrategy(max_size=1000),
        "tag": TagStrategy(),
        "dependency": DependencyStrategy(),
        # Estratégias compostas
        "ttl_lru": CompositeStrategy(
            [TTLStrategy(default_ttl=3600), LRUStrategy(max_size=1000)]
        ),
        "ttl_lfu": CompositeStrategy(
            [TTLStrategy(default_ttl=3600), LFUStrategy(max_size=1000)]
        ),
    }


# Instância global
_invalidation_manager: Optional[InvalidationManager] = None


def get_invalidation_manager() -> InvalidationManager:
    """Obtém gerenciador de invalidação global."""
    global _invalidation_manager

    if _invalidation_manager is None:
        _invalidation_manager = InvalidationManager()

        # Registrar estratégias padrão
        strategies = create_default_strategies()
        for name, strategy in strategies.items():
            _invalidation_manager.register_strategy(name, strategy)

        # Definir estratégia padrão
        _invalidation_manager.set_active_strategy("ttl_lru")

    return _invalidation_manager


def reset_invalidation_manager():
    """Reseta gerenciador (para testes)."""
    global _invalidation_manager
    _invalidation_manager = None
