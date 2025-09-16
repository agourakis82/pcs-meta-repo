"""
Sistema H2 - Métricas de Cache

Módulo para coleta e análise de métricas de performance do cache.
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class CacheMetric:
    """Métrica individual de cache."""

    timestamp: datetime
    operation: str  # get, set, delete, hit, miss
    key: str
    backend: str
    duration_ms: float
    success: bool
    size_bytes: int = 0
    metadata: Dict[str, Any] = None


@dataclass
class CacheStats:
    """Estatísticas agregadas de cache."""

    total_requests: int
    hits: int
    misses: int
    hit_rate: float
    avg_response_time: float
    total_size_bytes: int
    backend_stats: Dict[str, Dict[str, Any]]
    top_keys: List[Dict[str, Any]]
    error_rate: float
    operations_per_second: float


class CacheMetrics:
    """Coletor de métricas de cache."""

    def __init__(self, max_metrics: int = 10000, history_hours: int = 24):
        self.max_metrics = max_metrics
        self.history_hours = history_hours

        # Armazenamento de métricas
        self.metrics: deque = deque(maxlen=max_metrics)
        self.lock = threading.RLock()

        # Contadores rápidos
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.key_access_count = defaultdict(int)
        self.key_sizes = defaultdict(int)
        self.backend_metrics = defaultdict(lambda: defaultdict(int))

        # Cache de estatísticas
        self._last_stats_calculation = None
        self._cached_stats = None
        self._stats_cache_duration = 5  # segundos

    def record_operation(
        self,
        operation: str,
        key: str,
        backend: str,
        duration_ms: float,
        success: bool = True,
        size_bytes: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Registra uma operação de cache."""
        with self.lock:
            # Criar métrica
            metric = CacheMetric(
                timestamp=datetime.now(),
                operation=operation,
                key=key,
                backend=backend,
                duration_ms=duration_ms,
                success=success,
                size_bytes=size_bytes,
                metadata=metadata or {},
            )

            # Adicionar à queue
            self.metrics.append(metric)

            # Atualizar contadores rápidos
            self.counters[f"{operation}_total"] += 1
            self.counters[f"{backend}_{operation}"] += 1

            if success:
                self.counters[f"{operation}_success"] += 1
            else:
                self.counters[f"{operation}_error"] += 1

            # Registrar tempo de resposta
            self.timers[operation].append(duration_ms)
            if len(self.timers[operation]) > 1000:  # Manter últimas 1000
                self.timers[operation] = self.timers[operation][-1000:]

            # Atualizar estatísticas por chave
            if operation in ["get", "set"]:
                self.key_access_count[key] += 1
                if size_bytes > 0:
                    self.key_sizes[key] = size_bytes

            # Atualizar métricas por backend
            self.backend_metrics[backend][operation] += 1
            if success:
                self.backend_metrics[backend][f"{operation}_success"] += 1

            # Invalidar cache de estatísticas
            self._cached_stats = None

    def record_hit(self, key: str, backend: str, duration_ms: float):
        """Registra cache hit."""
        self.record_operation("hit", key, backend, duration_ms, True)

    def record_miss(self, key: str, backend: str, duration_ms: float):
        """Registra cache miss."""
        self.record_operation("miss", key, backend, duration_ms, True)

    def record_set(
        self, key: str, backend: str, duration_ms: float, size_bytes: int = 0
    ):
        """Registra operação de set."""
        self.record_operation("set", key, backend, duration_ms, True, size_bytes)

    def record_get(self, key: str, backend: str, duration_ms: float, hit: bool):
        """Registra operação de get."""
        if hit:
            self.record_hit(key, backend, duration_ms)
        else:
            self.record_miss(key, backend, duration_ms)

    def record_delete(
        self, key: str, backend: str, duration_ms: float, success: bool = True
    ):
        """Registra operação de delete."""
        self.record_operation("delete", key, backend, duration_ms, success)

    def get_stats(self, use_cache: bool = True) -> CacheStats:
        """Obtém estatísticas agregadas."""
        with self.lock:
            # Verificar cache
            if (
                use_cache
                and self._cached_stats
                and self._last_stats_calculation
                and (datetime.now() - self._last_stats_calculation).seconds
                < self._stats_cache_duration
            ):
                return self._cached_stats

            # Calcular estatísticas
            stats = self._calculate_stats()

            # Atualizar cache
            self._cached_stats = stats
            self._last_stats_calculation = datetime.now()

            return stats

    def _calculate_stats(self) -> CacheStats:
        """Calcula estatísticas a partir das métricas."""
        # Filtrar métricas recentes
        cutoff_time = datetime.now() - timedelta(hours=self.history_hours)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return CacheStats(
                total_requests=0,
                hits=0,
                misses=0,
                hit_rate=0.0,
                avg_response_time=0.0,
                total_size_bytes=0,
                backend_stats={},
                top_keys=[],
                error_rate=0.0,
                operations_per_second=0.0,
            )

        # Calcular métricas básicas
        total_requests = len(recent_metrics)
        hits = len([m for m in recent_metrics if m.operation == "hit"])
        misses = len([m for m in recent_metrics if m.operation == "miss"])
        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0.0

        # Tempo de resposta médio
        durations = [m.duration_ms for m in recent_metrics if m.success]
        avg_response_time = sum(durations) / len(durations) if durations else 0.0

        # Tamanho total
        total_size_bytes = sum(self.key_sizes.values())

        # Taxa de erro
        errors = len([m for m in recent_metrics if not m.success])
        error_rate = errors / total_requests if total_requests > 0 else 0.0

        # Operações por segundo
        if recent_metrics:
            time_span = (
                recent_metrics[-1].timestamp - recent_metrics[0].timestamp
            ).total_seconds()
            operations_per_second = total_requests / time_span if time_span > 0 else 0.0
        else:
            operations_per_second = 0.0

        # Estatísticas por backend
        backend_stats = {}
        for backend, metrics in self.backend_metrics.items():
            backend_stats[backend] = dict(metrics)

        # Top chaves
        top_keys = sorted(
            [
                {
                    "key": key,
                    "access_count": count,
                    "size_bytes": self.key_sizes.get(key, 0),
                }
                for key, count in self.key_access_count.items()
            ],
            key=lambda x: x["access_count"],
            reverse=True,
        )[:10]

        return CacheStats(
            total_requests=total_requests,
            hits=hits,
            misses=misses,
            hit_rate=hit_rate,
            avg_response_time=avg_response_time,
            total_size_bytes=total_size_bytes,
            backend_stats=backend_stats,
            top_keys=top_keys,
            error_rate=error_rate,
            operations_per_second=operations_per_second,
        )

    def get_time_series(
        self, metric: str, interval_minutes: int = 5, hours: int = 1
    ) -> Dict[str, List]:
        """Obtém série temporal de uma métrica."""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]

            # Agrupar por intervalos
            intervals = {}
            interval_duration = timedelta(minutes=interval_minutes)

            for m in recent_metrics:
                # Calcular bucket do intervalo
                bucket_time = m.timestamp.replace(
                    minute=(m.timestamp.minute // interval_minutes) * interval_minutes,
                    second=0,
                    microsecond=0,
                )

                if bucket_time not in intervals:
                    intervals[bucket_time] = []
                intervals[bucket_time].append(m)

            # Calcular valores por intervalo
            timestamps = []
            values = []

            for bucket_time in sorted(intervals.keys()):
                bucket_metrics = intervals[bucket_time]

                if metric == "hit_rate":
                    hits = len([m for m in bucket_metrics if m.operation == "hit"])
                    misses = len([m for m in bucket_metrics if m.operation == "miss"])
                    value = hits / (hits + misses) if (hits + misses) > 0 else 0.0
                elif metric == "requests_per_minute":
                    value = len(bucket_metrics)
                elif metric == "avg_response_time":
                    durations = [m.duration_ms for m in bucket_metrics if m.success]
                    value = sum(durations) / len(durations) if durations else 0.0
                elif metric == "error_rate":
                    errors = len([m for m in bucket_metrics if not m.success])
                    value = errors / len(bucket_metrics) if bucket_metrics else 0.0
                else:
                    value = len([m for m in bucket_metrics if m.operation == metric])

                timestamps.append(bucket_time.isoformat())
                values.append(value)

            return {
                "timestamps": timestamps,
                "values": values,
                "metric": metric,
                "interval_minutes": interval_minutes,
            }

    def get_backend_comparison(self) -> Dict[str, Dict[str, float]]:
        """Compara performance entre backends."""
        with self.lock:
            comparison = {}

            for backend in self.backend_metrics.keys():
                backend_metrics = [m for m in self.metrics if m.backend == backend]

                if backend_metrics:
                    hits = len([m for m in backend_metrics if m.operation == "hit"])
                    misses = len([m for m in backend_metrics if m.operation == "miss"])
                    total_requests = hits + misses

                    durations = [m.duration_ms for m in backend_metrics if m.success]
                    avg_duration = sum(durations) / len(durations) if durations else 0.0

                    errors = len([m for m in backend_metrics if not m.success])
                    error_rate = (
                        errors / len(backend_metrics) if backend_metrics else 0.0
                    )

                    comparison[backend] = {
                        "hit_rate": hits / total_requests
                        if total_requests > 0
                        else 0.0,
                        "avg_response_time": avg_duration,
                        "error_rate": error_rate,
                        "total_requests": len(backend_metrics),
                    }

            return comparison

    def get_key_analytics(self, limit: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """Analisa patterns de uso das chaves."""
        with self.lock:
            # Chaves mais acessadas
            most_accessed = sorted(
                [
                    {"key": k, "access_count": v}
                    for k, v in self.key_access_count.items()
                ],
                key=lambda x: x["access_count"],
                reverse=True,
            )[:limit]

            # Chaves maiores
            largest_keys = sorted(
                [
                    {"key": k, "size_bytes": v}
                    for k, v in self.key_sizes.items()
                    if v > 0
                ],
                key=lambda x: x["size_bytes"],
                reverse=True,
            )[:limit]

            # Chaves com mais erros
            error_keys = defaultdict(int)
            for metric in self.metrics:
                if not metric.success:
                    error_keys[metric.key] += 1

            most_errors = sorted(
                [{"key": k, "error_count": v} for k, v in error_keys.items()],
                key=lambda x: x["error_count"],
                reverse=True,
            )[:limit]

            return {
                "most_accessed": most_accessed,
                "largest_keys": largest_keys,
                "most_errors": most_errors,
            }

    def clear_metrics(self):
        """Limpa todas as métricas."""
        with self.lock:
            self.metrics.clear()
            self.counters.clear()
            self.timers.clear()
            self.key_access_count.clear()
            self.key_sizes.clear()
            self.backend_metrics.clear()
            self._cached_stats = None

    def export_metrics(self, format: str = "json", hours: int = 1) -> Dict[str, Any]:
        """Exporta métricas em formato específico."""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]

            if format == "json":
                return {
                    "metadata": {
                        "exported_at": datetime.now().isoformat(),
                        "hours": hours,
                        "total_metrics": len(recent_metrics),
                    },
                    "stats": self.get_stats(use_cache=False).__dict__,
                    "time_series": {
                        "hit_rate": self.get_time_series("hit_rate", 5, hours),
                        "requests_per_minute": self.get_time_series(
                            "requests_per_minute", 5, hours
                        ),
                        "avg_response_time": self.get_time_series(
                            "avg_response_time", 5, hours
                        ),
                    },
                    "backend_comparison": self.get_backend_comparison(),
                    "key_analytics": self.get_key_analytics(),
                }
            else:
                raise ValueError(f"Unsupported export format: {format}")


# Instância global
_cache_metrics: Optional[CacheMetrics] = None


def get_cache_metrics() -> CacheMetrics:
    """Obtém instância global das métricas de cache."""
    global _cache_metrics

    if _cache_metrics is None:
        _cache_metrics = CacheMetrics()

    return _cache_metrics


def reset_cache_metrics():
    """Reseta instância global (para testes)."""
    global _cache_metrics
    _cache_metrics = None
