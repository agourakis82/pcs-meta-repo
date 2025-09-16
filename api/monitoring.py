"""
Sistema de Monitoramento Avançado D3 - PCS-HELIO MCP API.

Este módulo fornece monitoramento completo do sistema incluindo:
- Métricas de sistema em tempo real (CPU, memória, disco, rede)
- Health checks detalhados de componentes
- Sistema de alertas automático
- Coleta e agregação de métricas
- Dashboard de monitoramento
- Monitoramento de endpoints e performance
"""

import asyncio
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional

import psutil

from .logging import get_logger

logger = get_logger("monitoring")


class HealthStatus(str, Enum):
    """Status de saúde do sistema."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """Severidade dos alertas."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """Métricas do sistema."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    thread_count: int
    file_descriptors: Optional[int] = None
    load_average: Optional[List[float]] = None


@dataclass
class ComponentHealth:
    """Saúde de um componente específico."""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: Optional[float] = None
    last_check: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alerta do sistema."""
    id: str
    severity: AlertSeverity
    component: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EndpointMetrics:
    """Métricas de endpoint."""
    path: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    last_request: Optional[datetime] = None
    status_codes: Dict[str, int] = field(default_factory=dict)


class MetricsCollector:
    """Coletor de métricas do sistema."""
    
    def __init__(self):
        self.collection_interval = 30  # segundos
        self.metrics_history: deque[SystemMetrics] = deque(maxlen=1000)
        self.endpoint_metrics: Dict[str, EndpointMetrics] = {}
        self.is_collecting = False
        self._collection_task: Optional[asyncio.Task[None]] = None
        
    async def start_collection(self):
        """Inicia coleta de métricas."""
        if self.is_collecting:
            return
            
        self.is_collecting = True
        self._collection_task = asyncio.create_task(self._collect_metrics_loop())
        logger.info("Coleta de métricas iniciada")
        
    async def stop_collection(self):
        """Para coleta de métricas."""
        self.is_collecting = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Coleta de métricas parada")
        
    async def _collect_metrics_loop(self):
        """Loop de coleta de métricas."""
        while self.is_collecting:
            try:
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Log métricas críticas
                if metrics.cpu_percent > 80:
                    logger.warning(f"CPU usage high: {metrics.cpu_percent:.1f}%")
                if metrics.memory_percent > 85:
                    logger.warning(f"Memory usage high: {metrics.memory_percent:.1f}%")
                if metrics.disk_percent > 90:
                    logger.warning(f"Disk usage high: {metrics.disk_percent:.1f}%")
                    
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Erro na coleta de métricas: {e}")
                await asyncio.sleep(self.collection_interval)
                
    def _collect_system_metrics(self) -> SystemMetrics:
        """Coleta métricas atuais do sistema."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memória
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # Rede
            network = psutil.net_io_counters()
            
            # Processos
            process_count = len(psutil.pids())
            
            # Threads (aproximado)
            thread_count = threading.active_count()
            
            # File descriptors (Linux/Unix)
            file_descriptors = None
            try:
                if hasattr(os, 'getrlimit'):
                    import resource
                    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
                    current_fd = len(os.listdir('/proc/self/fd'))
                    file_descriptors = current_fd
            except Exception:
                pass
                
            # Load average (Linux/Unix)
            load_average = None
            if hasattr(psutil, 'getloadavg'):
                try:
                    load_average = list(psutil.getloadavg())
                except Exception:
                    pass
                    
            return SystemMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=memory_used_gb,
                memory_total_gb=memory_total_gb,
                disk_percent=disk.percent,
                disk_used_gb=disk_used_gb,
                disk_total_gb=disk_total_gb,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                process_count=process_count,
                thread_count=thread_count,
                file_descriptors=file_descriptors,
                load_average=load_average
            )
            
        except Exception as e:
            logger.error(f"Erro coletando métricas do sistema: {e}")
            raise
            
    def record_endpoint_request(self, path: str, method: str, status_code: int, 
                               response_time_ms: float, success: bool = True):
        """Registra métricas de requisição de endpoint."""
        key = f"{method}:{path}"
        
        if key not in self.endpoint_metrics:
            self.endpoint_metrics[key] = EndpointMetrics(
                path=path,
                method=method,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time_ms=0.0,
                min_response_time_ms=float('inf'),
                max_response_time_ms=0.0,
                status_codes={}
            )
            
        metrics = self.endpoint_metrics[key]
        metrics.total_requests += 1
        metrics.last_request = datetime.now(timezone.utc)
        
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
            
        # Atualizar tempos de resposta
        metrics.min_response_time_ms = min(metrics.min_response_time_ms, 
                                         response_time_ms)
        metrics.max_response_time_ms = max(metrics.max_response_time_ms, 
                                         response_time_ms)
        
        # Calcular nova média (aproximada)
        old_avg = metrics.avg_response_time_ms
        total_requests = metrics.total_requests
        metrics.avg_response_time_ms = (
            (old_avg * (total_requests - 1) + response_time_ms) / total_requests
        )
        
        # Status codes
        status_str = str(status_code)
        metrics.status_codes[status_str] = (
            metrics.status_codes.get(status_str, 0) + 1
        )
        
    def get_latest_metrics(self) -> Optional[SystemMetrics]:
        """Obtém as métricas mais recentes."""
        return self.metrics_history[-1] if self.metrics_history else None
        
    def get_metrics_history(self, hours: int = 24) -> List[SystemMetrics]:
        """Obtém histórico de métricas."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp >= cutoff]
        
    def get_endpoint_metrics(self) -> Dict[str, EndpointMetrics]:
        """Obtém métricas de todos os endpoints."""
        return self.endpoint_metrics.copy()


class HealthChecker:
    """Verificador de saúde dos componentes."""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.last_health_status: Dict[str, ComponentHealth] = {}
        
    def register_health_check(self, name: str, check_func: Callable):
        """Registra uma verificação de saúde."""
        self.health_checks[name] = check_func
        logger.info(f"Health check registrado: {name}")
        
    async def check_component_health(self, name: str) -> ComponentHealth:
        """Verifica saúde de um componente específico."""
        if name not in self.health_checks:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check não encontrado para {name}",
                last_check=datetime.now(timezone.utc)
            )
            
        start_time = time.time()
        
        try:
            check_func = self.health_checks[name]
            
            # Executar verificação (pode ser async ou sync)
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
                
            response_time_ms = (time.time() - start_time) * 1000
            
            # Resultado pode ser bool, dict, ou ComponentHealth
            if isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "OK" if result else "Check failed"
                health = ComponentHealth(
                    name=name,
                    status=status,
                    message=message,
                    response_time_ms=response_time_ms,
                    last_check=datetime.now(timezone.utc)
                )
            elif isinstance(result, dict):
                health = ComponentHealth(
                    name=name,
                    status=HealthStatus(result.get('status', 'unknown')),
                    message=result.get('message', 'No message'),
                    response_time_ms=response_time_ms,
                    last_check=datetime.now(timezone.utc),
                    metadata=result.get('metadata', {})
                )
            elif isinstance(result, ComponentHealth):
                result.response_time_ms = response_time_ms
                result.last_check = datetime.now(timezone.utc)
                health = result
            else:
                health = ComponentHealth(
                    name=name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Resultado inesperado: {type(result)}",
                    response_time_ms=response_time_ms,
                    last_check=datetime.now(timezone.utc)
                )
                
            self.last_health_status[name] = health
            return health
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            health = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Erro durante verificação: {e}",
                response_time_ms=response_time_ms,
                last_check=datetime.now(timezone.utc)
            )
            self.last_health_status[name] = health
            logger.error(f"Erro no health check {name}: {e}")
            return health
            
    async def check_all_components(self) -> Dict[str, ComponentHealth]:
        """Verifica saúde de todos os componentes."""
        results = {}
        
        for name in self.health_checks:
            results[name] = await self.check_component_health(name)
            
        return results
        
    def get_overall_health(self) -> HealthStatus:
        """Obtém status geral de saúde do sistema."""
        if not self.last_health_status:
            return HealthStatus.UNKNOWN
            
        statuses = [h.status for h in self.last_health_status.values()]
        
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN


class AlertManager:
    """Gerenciador de alertas."""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: List[Callable] = []
        self.is_monitoring = False
        self._monitoring_task: Optional[asyncio.Task] = None
        
    async def start_monitoring(self):
        """Inicia monitoramento de alertas."""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._alert_monitoring_loop())
        logger.info("Monitoramento de alertas iniciado")
        
    async def stop_monitoring(self):
        """Para monitoramento de alertas."""
        self.is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoramento de alertas parado")
        
    async def _alert_monitoring_loop(self):
        """Loop de monitoramento de alertas."""
        while self.is_monitoring:
            try:
                # Verificar regras de alerta
                for rule_func in self.alert_rules:
                    try:
                        if asyncio.iscoroutinefunction(rule_func):
                            await rule_func(self)
                        else:
                            rule_func(self)
                    except Exception as e:
                        logger.error(f"Erro executando regra de alerta: {e}")
                        
                await asyncio.sleep(60)  # Verificar a cada minuto
                
            except Exception as e:
                logger.error(f"Erro no monitoramento de alertas: {e}")
                await asyncio.sleep(60)
                
    def add_alert_rule(self, rule_func: Callable):
        """Adiciona uma regra de alerta."""
        self.alert_rules.append(rule_func)
        logger.info(f"Regra de alerta adicionada: {rule_func.__name__}")
        
    def trigger_alert(self, alert_id: str, severity: AlertSeverity, 
                     component: str, message: str, metadata: Dict[str, Any] = None):
        """Dispara um alerta."""
        alert = Alert(
            id=alert_id,
            severity=severity,
            component=component,
            message=message,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        
        self.alerts[alert_id] = alert
        
        # Log alerta
        log_level = {
            AlertSeverity.INFO: "info",
            AlertSeverity.WARNING: "warning", 
            AlertSeverity.ERROR: "error",
            AlertSeverity.CRITICAL: "error"
        }.get(severity, "warning")
        
        getattr(logger, log_level)(
            f"ALERTA {severity.upper()}: {component} - {message}",
            extra={"alert_id": alert_id, "metadata": metadata}
        )
        
    def resolve_alert(self, alert_id: str):
        """Resolve um alerta."""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolved_at = datetime.now(timezone.utc)
            logger.info(f"Alerta resolvido: {alert_id}")
            
    def get_active_alerts(self, 
                         severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Obtém alertas ativos."""
        alerts = [a for a in self.alerts.values() if not a.resolved]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
            
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
        
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Obtém histórico de alertas."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        alerts = [a for a in self.alerts.values() if a.timestamp >= cutoff]
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)


# Instâncias globais
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
alert_manager = AlertManager()


async def initialize_monitoring():
    """Inicializa sistema de monitoramento."""
    try:
        # Registrar health checks padrão
        _register_default_health_checks()
        
        # Registrar regras de alerta padrão
        _register_default_alert_rules()
        
        # Iniciar coleta de métricas
        await metrics_collector.start_collection()
        
        # Iniciar monitoramento de alertas
        await alert_manager.start_monitoring()
        
        logger.info("Sistema de monitoramento inicializado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro inicializando monitoramento: {e}")
        raise


async def shutdown_monitoring():
    """Finaliza sistema de monitoramento."""
    try:
        await metrics_collector.stop_collection()
        await alert_manager.stop_monitoring()
        logger.info("Sistema de monitoramento finalizado")
    except Exception as e:
        logger.error(f"Erro finalizando monitoramento: {e}")


def _register_default_health_checks():
    """Registra health checks padrão."""
    
    def check_disk_space():
        """Verifica espaço em disco."""
        disk = psutil.disk_usage('/')
        percent_used = (disk.used / disk.total) * 100
        
        if percent_used > 95:
            return {
                'status': 'unhealthy',
                'message': f'Disk usage critical: {percent_used:.1f}%'
            }
        elif percent_used > 85:
            return {
                'status': 'degraded', 
                'message': f'Disk usage high: {percent_used:.1f}%'
            }
        else:
            return {
                'status': 'healthy',
                'message': f'Disk usage normal: {percent_used:.1f}%'
            }
            
    def check_memory():
        """Verifica uso de memória."""
        memory = psutil.virtual_memory()
        percent_used = memory.percent
        
        if percent_used > 90:
            return {
                'status': 'unhealthy',
                'message': f'Memory usage critical: {percent_used:.1f}%'
            }
        elif percent_used > 80:
            return {
                'status': 'degraded',
                'message': f'Memory usage high: {percent_used:.1f}%'
            }
        else:
            return {
                'status': 'healthy',
                'message': f'Memory usage normal: {percent_used:.1f}%'
            }
            
    def check_cpu():
        """Verifica uso de CPU."""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 95:
            return {
                'status': 'unhealthy',
                'message': f'CPU usage critical: {cpu_percent:.1f}%'
            }
        elif cpu_percent > 85:
            return {
                'status': 'degraded',
                'message': f'CPU usage high: {cpu_percent:.1f}%'
            }
        else:
            return {
                'status': 'healthy',
                'message': f'CPU usage normal: {cpu_percent:.1f}%'
            }
            
    health_checker.register_health_check("disk_space", check_disk_space)
    health_checker.register_health_check("memory_usage", check_memory)
    health_checker.register_health_check("cpu_usage", check_cpu)


def _register_default_alert_rules():
    """Registra regras de alerta padrão."""
    
    def check_system_resources(alert_mgr: AlertManager):
        """Verifica recursos do sistema para alertas."""
        latest_metrics = metrics_collector.get_latest_metrics()
        if not latest_metrics:
            return
            
        # Alerta de CPU
        if latest_metrics.cpu_percent > 90:
            alert_mgr.trigger_alert(
                alert_id="high_cpu_usage",
                severity=AlertSeverity.ERROR,
                component="system",
                message=f"CPU usage muito alto: {latest_metrics.cpu_percent:.1f}%",
                metadata={"cpu_percent": latest_metrics.cpu_percent}
            )
        elif latest_metrics.cpu_percent < 80:
            alert_mgr.resolve_alert("high_cpu_usage")
            
        # Alerta de memória
        if latest_metrics.memory_percent > 85:
            alert_mgr.trigger_alert(
                alert_id="high_memory_usage",
                severity=AlertSeverity.WARNING,
                component="system",
                message=f"Memory usage alto: {latest_metrics.memory_percent:.1f}%",
                metadata={"memory_percent": latest_metrics.memory_percent}
            )
        elif latest_metrics.memory_percent < 75:
            alert_mgr.resolve_alert("high_memory_usage")
            
        # Alerta de disco
        if latest_metrics.disk_percent > 90:
            alert_mgr.trigger_alert(
                alert_id="high_disk_usage",
                severity=AlertSeverity.CRITICAL,
                component="system",
                message=f"Disk usage crítico: {latest_metrics.disk_percent:.1f}%",
                metadata={"disk_percent": latest_metrics.disk_percent}
            )
        elif latest_metrics.disk_percent < 85:
            alert_mgr.resolve_alert("high_disk_usage")
            
    alert_manager.add_alert_rule(check_system_resources)


# Funções helper para fácil uso
async def get_system_health() -> Dict[str, Any]:
    """Obtém status geral de saúde do sistema."""
    health_results = await health_checker.check_all_components()
    overall_status = health_checker.get_overall_health()
    latest_metrics = metrics_collector.get_latest_metrics()
    active_alerts = alert_manager.get_active_alerts()
    
    return {
        "overall_status": overall_status,
        "components": {name: {
            "status": health.status,
            "message": health.message,
            "response_time_ms": health.response_time_ms,
            "last_check": health.last_check.isoformat() if health.last_check else None
        } for name, health in health_results.items()},
        "metrics": {
            "timestamp": latest_metrics.timestamp.isoformat() if latest_metrics else None,
            "cpu_percent": latest_metrics.cpu_percent if latest_metrics else None,
            "memory_percent": latest_metrics.memory_percent if latest_metrics else None,
            "disk_percent": latest_metrics.disk_percent if latest_metrics else None
        } if latest_metrics else None,
        "active_alerts": len(active_alerts),
        "critical_alerts": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL])
    }


async def get_detailed_metrics() -> Dict[str, Any]:
    """Obtém métricas detalhadas do sistema."""
    latest_metrics = metrics_collector.get_latest_metrics()
    endpoint_metrics = metrics_collector.get_endpoint_metrics()
    
    if not latest_metrics:
        return {"error": "No metrics available"}
        
    return {
        "system": {
            "timestamp": latest_metrics.timestamp.isoformat(),
            "cpu": {
                "percent": latest_metrics.cpu_percent,
                "load_average": latest_metrics.load_average
            },
            "memory": {
                "percent": latest_metrics.memory_percent,
                "used_gb": round(latest_metrics.memory_used_gb, 2),
                "total_gb": round(latest_metrics.memory_total_gb, 2)
            },
            "disk": {
                "percent": latest_metrics.disk_percent,
                "used_gb": round(latest_metrics.disk_used_gb, 2),
                "total_gb": round(latest_metrics.disk_total_gb, 2)
            },
            "network": {
                "bytes_sent": latest_metrics.network_bytes_sent,
                "bytes_recv": latest_metrics.network_bytes_recv
            },
            "processes": {
                "count": latest_metrics.process_count,
                "threads": latest_metrics.thread_count,
                "file_descriptors": latest_metrics.file_descriptors
            }
        },
        "endpoints": {
            key: {
                "path": metrics.path,
                "method": metrics.method,
                "total_requests": metrics.total_requests,
                "success_rate": round(
                    metrics.successful_requests / metrics.total_requests * 100, 2
                ) if metrics.total_requests > 0 else 0,
                "avg_response_time_ms": round(metrics.avg_response_time_ms, 2),
                "min_response_time_ms": round(metrics.min_response_time_ms, 2),
                "max_response_time_ms": round(metrics.max_response_time_ms, 2),
                "last_request": metrics.last_request.isoformat() if metrics.last_request else None,
                "status_codes": metrics.status_codes
            } for key, metrics in endpoint_metrics.items()
        }
    }


async def get_alerts_summary() -> Dict[str, Any]:
    """Obtém resumo de alertas."""
    active_alerts = alert_manager.get_active_alerts()
    recent_history = alert_manager.get_alert_history(hours=24)
    
    return {
        "active_alerts": {
            "total": len(active_alerts),
            "by_severity": {
                severity.value: len([a for a in active_alerts if a.severity == severity])
                for severity in AlertSeverity
            },
            "alerts": [{
                "id": alert.id,
                "severity": alert.severity,
                "component": alert.component,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            } for alert in active_alerts[:10]]  # Últimos 10
        },
        "recent_history": {
            "last_24h": len(recent_history),
            "resolved_last_24h": len([a for a in recent_history if a.resolved])
        }
    }    }