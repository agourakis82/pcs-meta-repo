"""
Sistema H1 - Router de Monitoramento e Métricas

Endpoints para exposição de métricas e dashboards de monitoramento.
"""

import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from . import (
    AlertManager,
    DashboardManager,
    HealthChecker,
    StructuredLogger,
    get_metrics_collector,
    get_performance_monitor,
)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

# Instâncias dos componentes
health_checker = HealthChecker()
alert_manager = AlertManager()
dashboard_manager = DashboardManager()
logger = StructuredLogger("monitoring_api")


@router.get("/health", summary="Verificação de saúde do sistema")
async def health_check():
    """
    Endpoint para verificação de saúde completa do sistema.
    
    Returns:
        Dict: Status de saúde detalhado de todos os componentes
    """
    try:
        health_result = await health_checker.check_all_health()
        
        # Log da verificação
        logger.info("Health check realizado", extra={
            "overall_status": health_result["overall_status"],
            "services_count": len(health_result["services"])
        })
        
        return JSONResponse(
            content=health_result,
            status_code=200 if health_result["overall_status"] == "healthy" else 503
        )
    except Exception as e:
        logger.error(f"Erro na verificação de saúde: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{service}", summary="Verificação de saúde específica")
async def health_check_service(service: str):
    """
    Endpoint para verificação de saúde de um serviço específico.
    
    Args:
        service: Nome do serviço (system, database, api)
    
    Returns:
        Dict: Status de saúde do serviço específico
    """
    try:
        if service == "system":
            result = await health_checker.check_system_health()
        elif service == "database":
            result = await health_checker.check_database_health()
        elif service == "api":
            result = await health_checker.check_api_health()
        else:
            raise HTTPException(status_code=404, detail=f"Serviço '{service}' não encontrado")
        
        logger.info(f"Health check do serviço {service}", extra={
            "service": service,
            "status": result["status"]
        })
        
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na verificação de saúde do serviço {service}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", summary="Métricas do sistema")
async def get_metrics():
    """
    Endpoint para obter todas as métricas coletadas.
    
    Returns:
        Dict: Resumo completo das métricas
    """
    try:
        collector = get_metrics_collector()
        metrics_summary = collector.get_summary()
        
        logger.info("Métricas solicitadas", extra={
            "total_requests": metrics_summary.get("request_stats", {}).get("total_requests", 0),
            "counters_count": len(metrics_summary.get("counters", {})),
            "gauges_count": len(metrics_summary.get("gauges", {}))
        })
        
        return JSONResponse(content=metrics_summary)
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/performance", summary="Estatísticas de performance")
async def get_performance_stats():
    """
    Endpoint para obter estatísticas atuais de performance.
    
    Returns:
        PerformanceStats: Estatísticas de CPU, memória, disco e requests
    """
    try:
        monitor = get_performance_monitor()
        stats = monitor.get_current_stats()
        
        # Converter dataclass para dict
        stats_dict = {
            "cpu_percent": stats.cpu_percent,
            "memory_percent": stats.memory_percent,
            "memory_used_mb": stats.memory_used_mb,
            "disk_usage_percent": stats.disk_usage_percent,
            "request_count": stats.request_count,
            "avg_response_time": stats.avg_response_time,
            "error_rate": stats.error_rate,
            "active_connections": stats.active_connections,
            "timestamp": stats.timestamp.isoformat()
        }
        
        logger.info("Estatísticas de performance solicitadas", extra={
            "cpu_percent": stats.cpu_percent,
            "memory_percent": stats.memory_percent,
            "request_count": stats.request_count
        })
        
        return JSONResponse(content=stats_dict)
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", summary="Alertas ativos")
async def get_active_alerts():
    """
    Endpoint para obter lista de alertas ativos.
    
    Returns:
        List: Lista de alertas ativos
    """
    try:
        # Verificar alertas baseado nas métricas atuais
        monitor = get_performance_monitor()
        stats = monitor.get_current_stats()
        
        # Simular verificação de alertas
        stats_dict = {
            "cpu_percent": stats.cpu_percent,
            "memory_percent": stats.memory_percent,
            "disk_usage_percent": stats.disk_usage_percent,
            "error_rate": stats.error_rate,
            "avg_response_time": stats.avg_response_time
        }
        
        alerts = alert_manager.check_alerts(stats_dict)
        
        logger.info("Alertas verificados", extra={
            "active_alerts_count": len(alerts),
            "stats_checked": True
        })
        
        return JSONResponse(content={"active_alerts": alerts})
    except Exception as e:
        logger.error(f"Erro ao verificar alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard", summary="Dashboard de monitoramento")
async def get_dashboard():
    """
    Endpoint para obter dados do dashboard de monitoramento.
    
    Returns:
        Dict: Dados do dashboard com widgets e métricas
    """
    try:
        # Gerar dados do dashboard
        dashboard_data = dashboard_manager.generate_dashboard_data()
        
        logger.info("Dashboard gerado", extra={
            "widgets_count": len(dashboard_data.get("widgets", [])),
            "overview_included": "overview" in dashboard_data
        })
        
        return JSONResponse(content=dashboard_data)
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/start", summary="Iniciar monitoramento")
async def start_monitoring():
    """
    Endpoint para iniciar o monitoramento contínuo do sistema.
    
    Returns:
        Dict: Status de inicialização
    """
    try:
        monitor = get_performance_monitor()
        await monitor.start_monitoring()
        
        logger.info("Monitoramento iniciado", extra={
            "monitoring_active": True,
            "collection_interval": monitor.collection_interval
        })
        
        return JSONResponse(content={
            "status": "started",
            "message": "Monitoramento iniciado com sucesso",
            "collection_interval": monitor.collection_interval
        })
    except Exception as e:
        logger.error(f"Erro ao iniciar monitoramento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/stop", summary="Parar monitoramento")
async def stop_monitoring():
    """
    Endpoint para parar o monitoramento contínuo do sistema.
    
    Returns:
        Dict: Status de parada
    """
    try:
        monitor = get_performance_monitor()
        await monitor.stop_monitoring()
        
        logger.info("Monitoramento parado", extra={
            "monitoring_active": False
        })
        
        return JSONResponse(content={
            "status": "stopped",
            "message": "Monitoramento parado com sucesso"
        })
    except Exception as e:
        logger.error(f"Erro ao parar monitoramento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/metrics", summary="Limpar métricas")
async def clear_metrics():
    """
    Endpoint para limpar todas as métricas coletadas.
    
    Returns:
        Dict: Confirmação de limpeza
    """
    try:
        collector = get_metrics_collector()
        collector.clear_metrics()
        
        logger.info("Métricas limpas", extra={
            "action": "clear_metrics",
            "metrics_cleared": True
        })
        
        return JSONResponse(content={
            "status": "cleared",
            "message": "Todas as métricas foram limpas com sucesso"
        })
    except Exception as e:
        logger.error(f"Erro ao limpar métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Middleware para coleta de métricas de requests
@router.middleware("http")
async def metrics_middleware(request, call_next):
    """
    Middleware para coleta automática de métricas de requests.
    """
    start_time = asyncio.get_event_loop().time()
    collector = get_metrics_collector()
    
    # Iniciar tracking do request
    collector.start_request()
    
    try:
        response = await call_next(request)
        
        # Calcular duração
        duration = asyncio.get_event_loop().time() - start_time
        
        # Registrar métricas
        collector.record_request(duration, response.status_code)
        
        return response
    except Exception as e:
        # Registrar erro
        duration = asyncio.get_event_loop().time() - start_time
        collector.record_request(duration, 500)
        raise
    finally:
        # Finalizar tracking do request
        collector.end_request()        collector.end_request()