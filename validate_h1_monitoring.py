#!/usr/bin/env python3
"""
Script de Validação - Sistema H1 Monitoramento e Métricas

Testa todos os componentes do sistema de monitoramento.
"""

import asyncio
import sys
import os
from datetime import datetime

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.monitoring import (
        get_metrics_collector,
        get_performance_monitor,
        HealthChecker,
        AlertManager,
        DashboardManager,
        StructuredLogger
    )
    print("✅ Imports do sistema de monitoramento OK")
except ImportError as e:
    print(f"❌ Erro no import: {e}")
    sys.exit(1)


async def test_metrics_collector():
    """Testa o coletor de métricas."""
    print("\n🔍 Testando MetricsCollector...")
    
    collector = get_metrics_collector()
    
    # Testar contadores
    collector.increment_counter("test_counter", 5.0)
    collector.increment_counter("test_counter", 3.0)
    
    # Testar gauges
    collector.set_gauge("test_gauge", 42.5)
    
    # Testar timers
    collector.record_timer("test_timer", 0.123)
    collector.record_timer("test_timer", 0.456)
    
    # Testar requests
    collector.record_request(0.234, 200)
    collector.record_request(0.567, 404)
    
    # Obter resumo
    summary = collector.get_summary()
    
    # Validações
    assert summary["counters"]["test_counter"] == 8.0, "Contador incorreto"
    assert summary["gauges"]["test_gauge"] == 42.5, "Gauge incorreto"
    assert summary["timers_stats"]["test_timer"]["count"] == 2, "Timer incorreto"
    assert summary["request_stats"]["total_requests"] == 2, "Requests incorretos"
    
    print("✅ MetricsCollector funcionando corretamente")
    return True


async def test_performance_monitor():
    """Testa o monitor de performance."""
    print("\n🔍 Testando PerformanceMonitor...")
    
    monitor = get_performance_monitor()
    
    # Coletar métricas do sistema
    await monitor.collect_system_metrics()
    
    # Obter estatísticas atuais
    stats = monitor.get_current_stats()
    
    # Validações básicas
    assert stats.cpu_percent >= 0.0, "CPU percent inválido"
    assert stats.memory_percent >= 0.0, "Memory percent inválido"
    assert stats.memory_used_mb >= 0.0, "Memory used inválido"
    assert stats.disk_usage_percent >= 0.0, "Disk usage inválido"
    assert isinstance(stats.timestamp, datetime), "Timestamp inválido"
    
    print("✅ PerformanceMonitor funcionando corretamente")
    return True


async def test_health_checker():
    """Testa o verificador de saúde."""
    print("\n🔍 Testando HealthChecker...")
    
    checker = HealthChecker()
    
    # Testar verificação do sistema
    system_health = await checker.check_system_health()
    assert system_health.status.value in ["healthy", "warning", "critical"], "Status inválido"
    
    # Testar verificação da API
    api_health = await checker.check_api_health()
    assert api_health.status.value in ["healthy", "warning", "critical"], "Status da API inválido"
    
    # Testar verificação completa
    all_health = await checker.check_all_health()
    assert "overall_status" in all_health, "Verificação completa inválida"
    assert "services" in all_health, "Services não encontrados"
    
    print("✅ HealthChecker funcionando corretamente")
    return True


async def test_alert_manager():
    """Testa o gerenciador de alertas."""
    print("\n🔍 Testando AlertManager...")
    
    manager = AlertManager()
    
    # Testar com dados normais
    normal_data = {
        "cpu_percent": 30.0,
        "memory_percent": 40.0,
        "disk_usage_percent": 50.0,
        "error_rate": 0.01,
        "avg_response_time": 0.1
    }
    
    alerts_normal = manager.check_alerts(normal_data)
    
    # Testar com dados problemáticos
    problem_data = {
        "cpu_percent": 95.0,
        "memory_percent": 90.0,
        "disk_usage_percent": 85.0,
        "error_rate": 0.15,
        "avg_response_time": 2.5
    }
    
    alerts_problem = manager.check_alerts(problem_data)
    
    # Validações
    assert isinstance(alerts_normal, list), "Alertas normais deve ser lista"
    assert isinstance(alerts_problem, list), "Alertas problemáticos deve ser lista"
    assert len(alerts_problem) > len(alerts_normal), "Deve haver mais alertas com problemas"
    
    print("✅ AlertManager funcionando corretamente")
    return True


async def test_dashboard_manager():
    """Testa o gerenciador de dashboard."""
    print("\n🔍 Testando DashboardManager...")
    
    manager = DashboardManager()
    
    # Gerar dados do dashboard
    dashboard_data = manager.generate_dashboard_data()
    
    # Validações
    assert "overview" in dashboard_data, "Overview não encontrado"
    assert "widgets" in dashboard_data, "Widgets não encontrados"
    assert len(dashboard_data["widgets"]) > 0, "Nenhum widget gerado"
    
    # Validar estrutura dos widgets
    for widget in dashboard_data["widgets"]:
        assert "id" in widget, "Widget sem ID"
        assert "type" in widget, "Widget sem tipo"
        assert "title" in widget, "Widget sem título"
        assert "data" in widget, "Widget sem dados"
    
    print("✅ DashboardManager funcionando corretamente")
    return True


async def test_structured_logger():
    """Testa o logger estruturado."""
    print("\n🔍 Testando StructuredLogger...")
    
    logger = StructuredLogger("test_module")
    
    # Testar diferentes níveis de log
    logger.info("Teste de log info", extra={"test_field": "test_value"})
    logger.warning("Teste de log warning")
    logger.error("Teste de log error")
    
    # Testar context manager de request
    with logger.request_context("test_request_123"):
        logger.info("Log dentro do contexto de request")
    
    # Testar timer de performance
    with logger.performance_timer("test_operation"):
        await asyncio.sleep(0.01)  # Simular operação
    
    print("✅ StructuredLogger funcionando corretamente")
    return True


async def test_integration():
    """Testa integração entre componentes."""
    print("\n🔍 Testando integração dos componentes...")
    
    # Obter instâncias
    collector = get_metrics_collector()
    monitor = get_performance_monitor()
    checker = HealthChecker()
    alert_manager = AlertManager()
    dashboard_manager = DashboardManager()
    
    # Iniciar monitoramento por um curto período
    await monitor.start_monitoring()
    await asyncio.sleep(2)  # Aguardar coleta
    await monitor.stop_monitoring()
    
    # Obter dados atuais
    stats = monitor.get_current_stats()
    
    # Verificar alertas baseados nos dados reais
    stats_dict = {
        "cpu_percent": stats.cpu_percent,
        "memory_percent": stats.memory_percent,
        "disk_usage_percent": stats.disk_usage_percent,
        "error_rate": stats.error_rate,
        "avg_response_time": stats.avg_response_time
    }
    
    alerts = alert_manager.check_alerts(stats_dict)
    
    # Gerar dashboard com dados reais
    dashboard_data = dashboard_manager.generate_dashboard_data()
    
    # Verificar saúde
    health = await checker.check_all_health()
    
    # Validações de integração
    assert stats.cpu_percent >= 0, "Stats inválidas"
    assert isinstance(alerts, list), "Alertas inválidos"
    assert "widgets" in dashboard_data, "Dashboard inválido"
    assert "overall_status" in health, "Health check inválido"
    
    print("✅ Integração funcionando corretamente")
    return True


async def main():
    """Função principal de validação."""
    print("🚀 Iniciando validação do Sistema H1 - Monitoramento e Métricas")
    print("=" * 70)
    
    tests = [
        test_metrics_collector,
        test_performance_monitor,
        test_health_checker,
        test_alert_manager,
        test_dashboard_manager,
        test_structured_logger,
        test_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Falha no teste {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Resultados da Validação:")
    print(f"   ✅ Testes aprovados: {passed}")
    print(f"   ❌ Testes falharam: {failed}")
    print(f"   📈 Taxa de sucesso: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 Sistema H1 - Monitoramento e Métricas VALIDADO com sucesso!")
        print("✨ Todos os componentes estão funcionando corretamente.")
        return 0
    else:
        print(f"\n⚠️  Sistema H1 tem {failed} problemas que precisam ser corrigidos.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Validação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erro fatal na validação: {e}")
        sys.exit(1)