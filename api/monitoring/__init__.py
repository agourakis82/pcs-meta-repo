"""
Sistema H1 - Monitoramento e Métricas

Módulo de inicialização do sistema de monitoramento.
"""

from .alerts import Alert, AlertManager, AlertSeverity
from .dashboard import DashboardManager
from .health import HealthChecker, HealthStatus, SystemHealth
from .logger import StructuredLogger
from .metrics import (
    MetricsCollector,
    PerformanceMonitor,
    get_metrics_collector,
    get_performance_monitor,
)

__all__ = [
    "MetricsCollector",
    "PerformanceMonitor",
    "get_metrics_collector",
    "get_performance_monitor",
    "HealthChecker",
    "SystemHealth",
    "AlertManager",
    "Alert",
    "DashboardManager",
    "StructuredLogger",
    "HealthStatus",
    "AlertSeverity",
]

# Lightweight, compatible singletons used by API routers
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
alert_manager = AlertManager()


async def get_system_health():
    """Compat function: basic health aggregation."""
    system_check = await health_checker.check_system_health()
    overall_status = (
        "healthy"
        if system_check.status.name.lower() == "healthy"
        else system_check.status.name.lower()
    )
    return {
        "overall_status": overall_status,
        "components": {
            "system": {
                "status": system_check.status.name.lower(),
                "message": system_check.message,
                "details": system_check.details,
            }
        },
        "metrics": {
            "cpu": {"percent": system_check.details.get("cpu_percent")},
            "memory": {"percent": system_check.details.get("memory_percent")},
            "disk": {"percent": system_check.details.get("disk_percent")},
        },
        "active_alerts": len(alert_manager.alerts),
        "critical_alerts": sum(
            1
            for a in alert_manager.alerts.values()
            if a.severity.name.lower() in ("critical", "fatal")
        ),
    }


async def get_detailed_metrics():
    """Compat function: simplified metrics structure."""
    summary = metrics_collector.get_summary()
    return {
        "system": {
            "cpu": {"percent": summary.get("gauges", {}).get("system_cpu_percent")},
            "memory": {
                "percent": summary.get("gauges", {}).get("system_memory_percent")
            },
            "disk": {"percent": summary.get("gauges", {}).get("system_disk_percent")},
        },
        "endpoints": {},
    }


async def get_alerts_summary():
    """Compat function: summarize alerts."""
    return {
        "active_alerts": {
            "total": len(alert_manager.alerts),
            "alerts": [],
        },
        "recent_history": {},
    }


__all__ += [
    "metrics_collector",
    "health_checker",
    "alert_manager",
    "get_system_health",
    "get_detailed_metrics",
    "get_alerts_summary",
]


# Lifecycle hooks expected by api.main
async def initialize_monitoring():
    return None


async def shutdown_monitoring():
    return None


__all__ += ["initialize_monitoring", "shutdown_monitoring"]
