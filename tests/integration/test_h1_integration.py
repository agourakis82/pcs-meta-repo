"""
Testes de Integração - Sistema H1 (Monitoring)

Testes completos para validar o sistema de monitoramento,
incluindo coleta de métricas, alertas e dashboard.
"""

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging

from tests.test_framework import TestSuite, test_framework

logger = logging.getLogger(__name__)


class H1IntegrationTests:
    """Testes de integração para o Sistema H1."""
    
    @staticmethod
    async def setup():
        """Setup inicial para testes H1."""
        logger.info("Configurando ambiente de testes H1")
        # Configuração inicial se necessária
    
    @staticmethod
    async def teardown():
        """Limpeza após testes H1."""
        logger.info("Limpando ambiente de testes H1")
        # Limpeza se necessária
    
    @staticmethod
    async def test_h1_system_health():
        """Testa saúde geral do sistema H1."""
        try:
            from api.monitoring.health import get_system_health
            
            health = await get_system_health()
            
            # Verifica se retornou dados válidos
            assert isinstance(health, dict), "Health deve retornar um dicionário"
            assert "status" in health, "Health deve conter status"
            assert "timestamp" in health, "Health deve conter timestamp"
            
            return {
                "passed": True,
                "metrics": {
                    "health_status": health.get("status"),
                    "components_checked": len(health.get("components", {}))
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de health não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h1_metrics_collection():
        """Testa coleta de métricas do H1."""
        try:
            from api.monitoring.metrics import MetricsCollector
            
            collector = MetricsCollector()
            
            # Testa coleta de métricas básicas
            metrics = await collector.collect_system_metrics()
            
            assert isinstance(metrics, dict), "Métricas devem ser um dicionário"
            
            expected_metrics = ["cpu_usage", "memory_usage", "disk_usage"]
            for metric in expected_metrics:
                if metric not in metrics:
                    logger.warning(f"Métrica {metric} não encontrada")
            
            return {
                "passed": True,
                "metrics": {
                    "metrics_collected": len(metrics),
                    "cpu_usage": metrics.get("cpu_usage", 0),
                    "memory_usage": metrics.get("memory_usage", 0)
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de métricas não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h1_alerts_system():
        """Testa sistema de alertas do H1."""
        try:
            from api.monitoring.alerts import AlertManager
            
            alert_manager = AlertManager()
            
            # Testa criação de alerta
            test_alert = {
                "type": "test",
                "message": "Teste de integração",
                "severity": "info"
            }
            
            alert_id = await alert_manager.create_alert(**test_alert)
            
            assert alert_id is not None, "Alert ID deve ser retornado"
            
            # Testa recuperação de alertas
            alerts = await alert_manager.get_active_alerts()
            
            assert isinstance(alerts, list), "Alertas devem ser uma lista"
            
            return {
                "passed": True,
                "metrics": {
                    "alert_created": alert_id is not None,
                    "active_alerts": len(alerts)
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de alertas não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h1_dashboard_data():
        """Testa dados do dashboard H1."""
        try:
            from api.monitoring.dashboard import get_dashboard_data
            
            dashboard_data = await get_dashboard_data()
            
            assert isinstance(dashboard_data, dict), "Dashboard data deve ser um dicionário"
            
            expected_sections = ["system_overview", "metrics", "alerts"]
            sections_found = 0
            
            for section in expected_sections:
                if section in dashboard_data:
                    sections_found += 1
            
            return {
                "passed": sections_found > 0,
                "metrics": {
                    "sections_found": sections_found,
                    "total_sections": len(expected_sections),
                    "data_size": len(str(dashboard_data))
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de dashboard não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h1_performance_monitoring():
        """Testa monitoramento de performance H1."""
        try:
            from api.monitoring.performance import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            
            # Testa medição de performance
            start_time = time.time()
            
            # Simula operação monitorada
            async def dummy_operation():
                await asyncio.sleep(0.1)
                return "success"
            
            result = await monitor.measure_operation(dummy_operation)
            
            duration = time.time() - start_time
            
            assert "duration" in result, "Resultado deve conter duração"
            assert "result" in result, "Resultado deve conter resultado da operação"
            
            return {
                "passed": True,
                "metrics": {
                    "operation_duration": result.get("duration", 0),
                    "total_test_duration": duration,
                    "operation_success": result.get("result") == "success"
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de performance não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h1_integration_points():
        """Testa pontos de integração do H1 com outros sistemas."""
        try:
            # Testa se H1 pode ser importado e inicializado
            from api.monitoring import get_monitor
            
            monitor = get_monitor()
            
            # Verifica se monitor tem interfaces para outros sistemas
            has_h2_integration = hasattr(monitor, 'cache_monitor')
            has_h3_integration = hasattr(monitor, 'api_monitor')
            has_h4_integration = hasattr(monitor, 'data_processing_monitor')
            
            integrations_available = sum([
                has_h2_integration,
                has_h3_integration, 
                has_h4_integration
            ])
            
            return {
                "passed": integrations_available > 0,
                "metrics": {
                    "h2_integration": has_h2_integration,
                    "h3_integration": has_h3_integration,
                    "h4_integration": has_h4_integration,
                    "total_integrations": integrations_available
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo principal H1 não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }


# Registra a suite de testes H1
def register_h1_tests():
    """Registra todos os testes H1 no framework."""
    
    suite = TestSuite(
        name="h1_integration",
        description="Testes de integração do Sistema H1 (Monitoring)",
        setup_func=H1IntegrationTests.setup,
        teardown_func=H1IntegrationTests.teardown
    )
    
    # Adiciona todos os métodos de teste
    suite.tests = [
        H1IntegrationTests.test_h1_system_health,
        H1IntegrationTests.test_h1_metrics_collection,
        H1IntegrationTests.test_h1_alerts_system,
        H1IntegrationTests.test_h1_dashboard_data,
        H1IntegrationTests.test_h1_performance_monitoring,
        H1IntegrationTests.test_h1_integration_points
    ]
    
    test_framework.register_suite(suite)
    logger.info("Testes H1 registrados no framework")


# Função para executar apenas testes H1
async def run_h1_tests():
    """Executa apenas os testes H1."""
    register_h1_tests()
    
    results = await test_framework.run_suite("h1_integration")
    
    print("=" * 60)
    print("RESULTADOS DOS TESTES H1 (MONITORING)")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"Testes executados: {total}")
    print(f"Testes passaram: {passed}")
    print(f"Taxa de sucesso: {(passed/total*100):.1f}%")
    
    for result in results:
        status = "✅" if result.passed else "❌"
        print(f"{status} {result.test_name} ({result.duration:.2f}s)")
        if not result.passed:
            print(f"   Error: {result.error_message}")
    
    return passed == total


if __name__ == "__main__":
    # Executa testes H1 quando executado diretamente
    success = asyncio.run(run_h1_tests())
    exit(0 if success else 1)    exit(0 if success else 1)