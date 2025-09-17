"""
Sistema H1 - Coleta de Métricas e Performance

Módulo para coleta, armazenamento e análise de métricas de performance do sistema.
"""

import asyncio
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import psutil


@dataclass
class PerformanceStats:
    """Estatísticas de performance do sistema."""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    request_count: int
    avg_response_time: float
    error_rate: float
    active_connections: int
    timestamp: datetime


class MetricsCollector:
    """Coletor principal de métricas do sistema."""
    
    def __init__(self):
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.RLock()
        
        # Métricas de requests
        self.request_count = 0
        self.request_times: List[float] = []
        self.error_count = 0
        self.active_requests = 0
        
    def increment_counter(self, name: str, value: float = 1.0):
        """Incrementa um contador."""
        with self.lock:
            self.counters[name] += value
    
    def set_gauge(self, name: str, value: float):
        """Define valor de um gauge."""
        with self.lock:
            self.gauges[name] = value
    
    def record_timer(self, name: str, duration: float):
        """Registra tempo de execução."""
        with self.lock:
            self.timers[name].append(duration)
            # Manter apenas últimos 1000 valores
            if len(self.timers[name]) > 1000:
                self.timers[name] = self.timers[name][-1000:]
    
    def record_request(self, duration: float, status_code: int):
        """Registra métricas de request."""
        with self.lock:
            self.request_count += 1
            self.request_times.append(duration)
            
            # Manter apenas últimos 1000 valores
            if len(self.request_times) > 1000:
                self.request_times = self.request_times[-1000:]
            
            if status_code >= 400:
                self.error_count += 1
                
            self.increment_counter("http_requests_total")
            self.record_timer("http_request_duration", duration)
    
    def start_request(self):
        """Marca início de request."""
        with self.lock:
            self.active_requests += 1
            self.set_gauge("http_active_requests", self.active_requests)
    
    def end_request(self):
        """Marca fim de request."""
        with self.lock:
            self.active_requests = max(0, self.active_requests - 1)
            self.set_gauge("http_active_requests", self.active_requests)
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtém resumo das métricas."""
        with self.lock:
            avg_response_time = 0.0
            if self.request_times:
                avg_response_time = sum(self.request_times) / len(self.request_times)
            
            error_rate = 0.0
            if self.request_count > 0:
                error_rate = self.error_count / self.request_count
            
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "timers_stats": {
                    name: {
                        "count": len(values),
                        "avg": sum(values) / len(values) if values else 0,
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0
                    }
                    for name, values in self.timers.items()
                },
                "request_stats": {
                    "total_requests": self.request_count,
                    "avg_response_time": avg_response_time,
                    "error_rate": error_rate,
                    "active_requests": self.active_requests
                }
            }
    
    def clear_metrics(self):
        """Limpa todas as métricas coletadas."""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.timers.clear()


class PerformanceMonitor:
    """Monitor de performance do sistema."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.is_running = False
        self.collection_interval = 30  # seconds
        
    async def start_monitoring(self):
        """Inicia monitoramento contínuo."""
        if self.is_running:
            return
            
        self.is_running = True
        asyncio.create_task(self._monitor_loop())
        
    async def stop_monitoring(self):
        """Para monitoramento."""
        self.is_running = False
    
    async def _monitor_loop(self):
        """Loop principal de monitoramento."""
        while self.is_running:
            try:
                await self.collect_system_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Erro no monitoramento: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def collect_system_metrics(self):
        """Coleta métricas do sistema."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.set_gauge("system_cpu_percent", cpu_percent)
            
            # Memória
            memory = psutil.virtual_memory()
            self.metrics.set_gauge("system_memory_percent", memory.percent)
            self.metrics.set_gauge("system_memory_used_mb", memory.used / 1024 / 1024)
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.metrics.set_gauge("system_disk_percent", disk_percent)
            
        except Exception as e:
            print(f"Erro coletando métricas do sistema: {e}")
    
    def get_current_stats(self) -> PerformanceStats:
        """Obtém estatísticas atuais de performance."""
        try:
            # Coletar dados do sistema
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Obter métricas de requests
            summary = self.metrics.get_summary()
            request_stats = summary.get("request_stats", {})
            
            return PerformanceStats(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                disk_usage_percent=(disk.used / disk.total) * 100,
                request_count=request_stats.get("total_requests", 0),
                avg_response_time=request_stats.get("avg_response_time", 0),
                error_rate=request_stats.get("error_rate", 0),
                active_connections=request_stats.get("active_requests", 0),
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"Erro obtendo estatísticas: {e}")
            return PerformanceStats(
                cpu_percent=0.0,
                memory_percent=0.0, 
                memory_used_mb=0.0,
                disk_usage_percent=0.0,
                request_count=0,
                avg_response_time=0.0,
                error_rate=0.0,
                active_connections=0,
                timestamp=datetime.now()
            )


# Instância global do coletor de métricas
_metrics_collector = MetricsCollector()
_performance_monitor = PerformanceMonitor(_metrics_collector)


def get_metrics_collector() -> MetricsCollector:
    """Obtém instância global do coletor de métricas."""
    return _metrics_collector


def get_performance_monitor() -> PerformanceMonitor:
    """Obtém instância global do monitor de performance."""
    return _performance_monitor