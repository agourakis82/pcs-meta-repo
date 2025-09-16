"""
Endpoints de Monitoramento D3 - PCS-HELIO MCP API.

Este módulo fornece endpoints REST para monitoramento do sistema:
- Health checks detalhados
- Métricas de sistema em tempo real
- Alertas ativos e histórico
- Dashboard de monitoramento
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from ..auth import get_api_key_required
from ..errors import NotFoundError
from ..logging import get_logger, log_performance_metric
from ..monitoring import (
    AlertSeverity,
    HealthStatus,
    alert_manager,
    get_alerts_summary,
    get_detailed_metrics,
    get_system_health,
    health_checker,
    metrics_collector,
)

logger = get_logger("monitoring_endpoints")

router = APIRouter(tags=["monitoring"])


class HealthCheckResponse(BaseModel):
    """Resposta de health check."""

    success: bool = Field(..., description="Status de sucesso")
    overall_status: HealthStatus = Field(..., description="Status geral do sistema")
    components: Dict[str, Any] = Field(..., description="Status dos componentes")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Métricas básicas")
    active_alerts: int = Field(..., description="Número de alertas ativos")
    critical_alerts: int = Field(..., description="Número de alertas críticos")
    timestamp: datetime = Field(..., description="Timestamp da verificação")


class DetailedMetricsResponse(BaseModel):
    """Resposta de métricas detalhadas."""

    success: bool = Field(..., description="Status de sucesso")
    system: Dict[str, Any] = Field(..., description="Métricas de sistema")
    endpoints: Dict[str, Any] = Field(..., description="Métricas de endpoints")
    timestamp: datetime = Field(..., description="Timestamp das métricas")


class AlertsResponse(BaseModel):
    """Resposta de alertas."""

    success: bool = Field(..., description="Status de sucesso")
    active_alerts: Dict[str, Any] = Field(..., description="Alertas ativos")
    recent_history: Dict[str, Any] = Field(..., description="Histórico recente")
    timestamp: datetime = Field(..., description="Timestamp da consulta")


class ComponentHealthResponse(BaseModel):
    """Resposta de health check de componente específico."""

    success: bool = Field(..., description="Status de sucesso")
    component: str = Field(..., description="Nome do componente")
    status: HealthStatus = Field(..., description="Status do componente")
    message: str = Field(..., description="Mensagem de status")
    response_time_ms: Optional[float] = Field(None, description="Tempo de resposta")
    last_check: Optional[datetime] = Field(None, description="Última verificação")
    metadata: Dict[str, Any] = Field(..., description="Metadados adicionais")
    timestamp: datetime = Field(..., description="Timestamp da verificação")


@router.get(
    "/health",
    summary="Health check geral do sistema",
    response_model=HealthCheckResponse,
)
async def get_health_status(
    request: Request, api_key: str = Depends(get_api_key_required)
) -> HealthCheckResponse:
    """
    Obtém status geral de saúde do sistema.

    Retorna informações sobre:
    - Status geral do sistema
    - Status de cada componente
    - Métricas básicas de sistema
    - Contagem de alertas
    """
    start_time = time.time()

    try:
        # Obter health status
        health_data = await get_system_health()

        # Log performance
        processing_time = time.time() - start_time
        log_performance_metric(
            metric_name="health_check_request",
            value=processing_time * 1000,
            unit="ms",
            context={
                "endpoint": "/monitoring/health",
                "overall_status": health_data["overall_status"],
            },
        )

        logger.info(
            "Health check realizado",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "overall_status": health_data["overall_status"],
                "active_alerts": health_data["active_alerts"],
                "processing_time": f"{processing_time:.3f}s",
            },
        )

        return HealthCheckResponse(
            success=True,
            overall_status=health_data["overall_status"],
            components=health_data["components"],
            metrics=health_data["metrics"],
            active_alerts=health_data["active_alerts"],
            critical_alerts=health_data["critical_alerts"],
            timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error(
            f"Erro no health check: {e}",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "error_type": type(e).__name__,
            },
        )
        raise NotFoundError(f"Erro obtendo health status: {e}")


@router.get(
    "/health/{component}",
    summary="Health check de componente específico",
    response_model=ComponentHealthResponse,
)
async def get_component_health(
    component: str, request: Request, api_key: str = Depends(get_api_key_required)
) -> ComponentHealthResponse:
    """
    Verifica saúde de um componente específico.

    Args:
        component: Nome do componente a verificar
    """
    start_time = time.time()

    try:
        # Verificar health do componente
        health = await health_checker.check_component_health(component)

        # Log performance
        processing_time = time.time() - start_time
        log_performance_metric(
            metric_name="component_health_request",
            value=processing_time * 1000,
            unit="ms",
            context={
                "endpoint": f"/monitoring/health/{component}",
                "component": component,
                "status": health.status,
            },
        )

        logger.info(
            "Component health check realizado",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "component": component,
                "status": health.status,
                "processing_time": f"{processing_time:.3f}s",
            },
        )

        return ComponentHealthResponse(
            success=True,
            component=health.name,
            status=health.status,
            message=health.message,
            response_time_ms=health.response_time_ms,
            last_check=health.last_check,
            metadata=health.metadata,
            timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error(
            f"Erro no component health check: {e}",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "component": component,
                "error_type": type(e).__name__,
            },
        )
        raise NotFoundError(f"Erro verificando componente {component}: {e}")


@router.get(
    "/metrics",
    summary="Métricas detalhadas do sistema",
    response_model=DetailedMetricsResponse,
)
async def get_system_metrics(
    request: Request, api_key: str = Depends(get_api_key_required)
) -> DetailedMetricsResponse:
    """
    Obtém métricas detalhadas do sistema.

    Retorna informações sobre:
    - CPU, memória, disco, rede
    - Contadores de processos e threads
    - Métricas de endpoints
    - Estatísticas de performance
    """
    start_time = time.time()

    try:
        # Obter métricas detalhadas
        metrics_data = await get_detailed_metrics()

        if "error" in metrics_data:
            raise NotFoundError(metrics_data["error"])

        # Log performance
        processing_time = time.time() - start_time
        log_performance_metric(
            metric_name="metrics_request",
            value=processing_time * 1000,
            unit="ms",
            context={
                "endpoint": "/monitoring/metrics",
                "endpoint_count": len(metrics_data.get("endpoints", {})),
            },
        )

        logger.info(
            "Métricas detalhadas obtidas",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "cpu_percent": metrics_data.get("system", {})
                .get("cpu", {})
                .get("percent"),
                "memory_percent": metrics_data.get("system", {})
                .get("memory", {})
                .get("percent"),
                "processing_time": f"{processing_time:.3f}s",
            },
        )

        return DetailedMetricsResponse(
            success=True,
            system=metrics_data["system"],
            endpoints=metrics_data["endpoints"],
            timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error(
            f"Erro obtendo métricas: {e}",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "error_type": type(e).__name__,
            },
        )
        raise NotFoundError(f"Erro obtendo métricas do sistema: {e}")


@router.get("/alerts", summary="Alertas do sistema", response_model=AlertsResponse)
async def get_system_alerts(
    request: Request,
    severity: Optional[AlertSeverity] = Query(
        None, description="Filtrar por severidade"
    ),
    api_key: str = Depends(get_api_key_required),
) -> AlertsResponse:
    """
    Obtém alertas ativos e histórico do sistema.

    Args:
        severity: Filtrar alertas por severidade (opcional)
    """
    start_time = time.time()

    try:
        # Obter resumo de alertas
        alerts_data = await get_alerts_summary()

        # Filtrar por severidade se especificado
        if severity:
            active_alerts = alert_manager.get_active_alerts(severity)
            alerts_data["active_alerts"]["alerts"] = [
                {
                    "id": alert.id,
                    "severity": alert.severity,
                    "component": alert.component,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata,
                }
                for alert in active_alerts[:10]
            ]  # Últimos 10

        # Log performance
        processing_time = time.time() - start_time
        log_performance_metric(
            metric_name="alerts_request",
            value=processing_time * 1000,
            unit="ms",
            context={
                "endpoint": "/monitoring/alerts",
                "severity_filter": severity.value if severity else None,
                "active_count": alerts_data["active_alerts"]["total"],
            },
        )

        logger.info(
            "Alertas obtidos",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "severity_filter": severity.value if severity else None,
                "active_alerts": alerts_data["active_alerts"]["total"],
                "processing_time": f"{processing_time:.3f}s",
            },
        )

        return AlertsResponse(
            success=True,
            active_alerts=alerts_data["active_alerts"],
            recent_history=alerts_data["recent_history"],
            timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error(
            f"Erro obtendo alertas: {e}",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "error_type": type(e).__name__,
            },
        )
        raise NotFoundError(f"Erro obtendo alertas do sistema: {e}")


@router.get(
    "/dashboard", summary="Dashboard de monitoramento", response_model=Dict[str, Any]
)
async def get_monitoring_dashboard(
    request: Request, api_key: str = Depends(get_api_key_required)
) -> Dict[str, Any]:
    """
    Obtém dados completos para dashboard de monitoramento.

    Combina health status, métricas e alertas em uma resposta única.
    """
    start_time = time.time()

    try:
        # Obter todos os dados em paralelo
        import asyncio

        health_task = asyncio.create_task(get_system_health())
        metrics_task = asyncio.create_task(get_detailed_metrics())
        alerts_task = asyncio.create_task(get_alerts_summary())

        health_data, metrics_data, alerts_data = await asyncio.gather(
            health_task, metrics_task, alerts_task
        )

        # Combinar dados
        dashboard_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": health_data,
            "metrics": metrics_data,
            "alerts": alerts_data,
            "summary": {
                "overall_status": health_data["overall_status"],
                "critical_alerts": health_data["critical_alerts"],
                "cpu_percent": metrics_data.get("system", {})
                .get("cpu", {})
                .get("percent"),
                "memory_percent": metrics_data.get("system", {})
                .get("memory", {})
                .get("percent"),
                "disk_percent": metrics_data.get("system", {})
                .get("disk", {})
                .get("percent"),
                "endpoint_count": len(metrics_data.get("endpoints", {})),
                "total_requests": sum(
                    endpoint.get("total_requests", 0)
                    for endpoint in metrics_data.get("endpoints", {}).values()
                ),
            },
        }

        # Log performance
        processing_time = time.time() - start_time
        log_performance_metric(
            metric_name="dashboard_request",
            value=processing_time * 1000,
            unit="ms",
            context={
                "endpoint": "/monitoring/dashboard",
                "overall_status": health_data["overall_status"],
            },
        )

        logger.info(
            "Dashboard obtido",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "overall_status": health_data["overall_status"],
                "processing_time": f"{processing_time:.3f}s",
            },
        )

        return dashboard_data

    except Exception as e:
        logger.error(
            f"Erro obtendo dashboard: {e}",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "error_type": type(e).__name__,
            },
        )
        raise NotFoundError(f"Erro obtendo dashboard de monitoramento: {e}")


# Middleware helper para registrar métricas de endpoints
class MonitoringMiddleware:
    """Middleware para registrar métricas de endpoints automaticamente."""

    def __init__(self):
        self.metrics_collector = metrics_collector

    async def __call__(self, request: Request, call_next):
        """Processar requisição e registrar métricas."""
        start_time = time.time()

        # Processar requisição
        response = await call_next(request)

        # Calcular tempo de resposta
        response_time_ms = (time.time() - start_time) * 1000

        # Registrar métricas
        success = 200 <= response.status_code < 400

        self.metrics_collector.record_endpoint_request(
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            success=success,
        )

        return response


# Instância do middleware
monitoring_middleware = MonitoringMiddleware()
