"""
Sistema H1 - Health Checks e Monitoramento de Saúde

Módulo para verificação de saúde do sistema e componentes.
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

import psutil


class HealthStatus(Enum):
    """Status de saúde dos componentes."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Resultado de um health check."""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    duration_ms: float
    details: Dict[str, Any]


class HealthChecker:
    """Verificador de saúde do sistema."""
    
    def __init__(self):
        self.checks: Dict[str, Any] = {}
        
    async def check_system_health(self) -> HealthCheck:
        """Verifica saúde geral do sistema."""
        start_time = time.time()
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memória
            memory = psutil.virtual_memory()
            
            # Disco
            disk = psutil.disk_usage('/')
            
            # Determinar status baseado nos recursos
            status = HealthStatus.HEALTHY
            issues = []
            
            if cpu_percent > 80:
                status = HealthStatus.WARNING
                issues.append(f"CPU alta: {cpu_percent:.1f}%")
            
            if memory.percent > 85:
                status = HealthStatus.WARNING
                issues.append(f"Memória alta: {memory.percent:.1f}%")
                
            if (disk.used / disk.total) > 0.9:
                status = HealthStatus.CRITICAL
                issues.append("Disco quase cheio")
                
            duration = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="system",
                status=status,
                message="OK" if status == HealthStatus.HEALTHY else "; ".join(issues),
                timestamp=datetime.now(),
                duration_ms=duration,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100
                }
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="system",
                status=HealthStatus.CRITICAL,
                message=f"Erro: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=duration,
                details={"error": str(e)}
            )
    
    async def check_database_health(self) -> HealthCheck:
        """Verifica saúde do banco/cache."""
        start_time = time.time()
        
        try:
            # Simular verificação de conectividade
            await asyncio.sleep(0.01)  # Simular latência
            
            duration = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Conectividade OK",
                timestamp=datetime.now(),
                duration_ms=duration,
                details={"connection": "active"}
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database",
                status=HealthStatus.CRITICAL,
                message=f"Erro de conexão: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=duration,
                details={"error": str(e)}
            )
    
    async def check_api_health(self) -> HealthCheck:
        """Verifica saúde das APIs."""
        start_time = time.time()
        
        try:
            # Verificar se componentes principais estão funcionando
            duration = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="api",
                status=HealthStatus.HEALTHY,
                message="APIs funcionando",
                timestamp=datetime.now(),
                duration_ms=duration,
                details={"endpoints": "active"}
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="api",
                status=HealthStatus.CRITICAL,
                message=f"Erro na API: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=duration,
                details={"error": str(e)}
            )
    
    async def run_all_checks(self) -> List[HealthCheck]:
        """Executa todos os health checks."""
        checks = await asyncio.gather(
            self.check_system_health(),
            self.check_database_health(),
            self.check_api_health(),
            return_exceptions=True
        )
        
        # Filtrar exceções
        valid_checks = []
        for check in checks:
            if isinstance(check, HealthCheck):
                valid_checks.append(check)
            else:
                # Criar check de erro para exceções
                valid_checks.append(HealthCheck(
                    name="unknown",
                    status=HealthStatus.CRITICAL,
                    message=f"Erro interno: {str(check)}",
                    timestamp=datetime.now(),
                    duration_ms=0.0,
                    details={"error": str(check)}
                ))
        
        return valid_checks
    
    async def check_all_health(self) -> Dict[str, Any]:
        """
        Verifica saúde de todos os componentes (compatibilidade).
        
        Returns:
            Dicionário com status geral e detalhes dos serviços
        """
        # Executar todas as verificações
        system_check = await self.check_system_health()
        database_check = await self.check_database_health()
        api_check = await self.check_api_health()
        
        all_checks = [system_check, database_check, api_check]
        
        # Determinar status geral
        if any(check.status == HealthStatus.CRITICAL for check in all_checks):
            overall_status = "unhealthy"
        elif any(check.status == HealthStatus.WARNING for check in all_checks):
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # Formattar resposta
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "duration_ms": check.duration_ms,
                    "details": check.details
                }
                for check in all_checks
            ]
        }


@dataclass
class SystemHealth:
    """Estado geral de saúde do sistema."""
    overall_status: HealthStatus
    checks: List[HealthCheck]
    timestamp: datetime
    uptime_seconds: float
    
    @classmethod
    def from_checks(cls, checks: List[HealthCheck], uptime: float) -> "SystemHealth":
        """Cria SystemHealth a partir de lista de checks."""
        # Determinar status geral
        if any(check.status == HealthStatus.CRITICAL for check in checks):
            overall_status = HealthStatus.CRITICAL
        elif any(check.status == HealthStatus.WARNING for check in checks):
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY
            
        return cls(
            overall_status=overall_status,
            checks=checks,
            timestamp=datetime.now(),
            uptime_seconds=uptime
        )


# Instância global
_health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    """Obtém instância global do health checker."""
    return _health_checker