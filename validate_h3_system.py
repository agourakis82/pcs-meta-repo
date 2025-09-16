"""
Sistema H3 - Validação Completa

Script de validação abrangente para todos os componentes do Sistema H3 de Integração e APIs.
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Contadores de validação
validation_results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}


def log_test_result(test_name: str, success: bool, details: str = ""):
    """Registra resultado de teste."""
    validation_results["total_tests"] += 1
    
    if success:
        validation_results["passed"] += 1
        logger.info(f"✅ {test_name} - PASSOU {details}")
    else:
        validation_results["failed"] += 1
        validation_results["errors"].append(f"{test_name}: {details}")
        logger.error(f"❌ {test_name} - FALHOU {details}")


async def validate_h1_monitoring_system():
    """Valida Sistema H1 - Monitoramento e Métricas."""
    logger.info("🔍 Validando H1 - Sistema de Monitoramento...")
    
    try:
        # Testar importação do sistema de monitoramento
        from monitoring import MetricsCollector, SystemMonitor, get_metrics_collector
        log_test_result("H1: Importação do sistema de monitoramento", True)
        
        # Testar criação de instância
        metrics = get_metrics_collector()
        log_test_result("H1: Criação de MetricsCollector", metrics is not None)
        
        # Testar coleta de métricas básicas
        await metrics.record_counter("test_counter", 1)
        await metrics.record_histogram("test_histogram", 0.5)
        log_test_result("H1: Gravação de métricas", True)
        
        # Testar recuperação de métricas
        metrics_data = await metrics.get_metrics()
        log_test_result("H1: Recuperação de métricas", isinstance(metrics_data, dict))
        
    except ImportError as e:
        log_test_result("H1: Sistema de monitoramento", False, f"ImportError: {e}")
    except Exception as e:
        log_test_result("H1: Sistema de monitoramento", False, f"Error: {e}")


async def validate_h2_cache_system():
    """Valida Sistema H2 - Cache e Performance."""
    logger.info("🔍 Validando H2 - Sistema de Cache...")
    
    try:
        # Testar importação do sistema de cache
        from cache import CacheManager, get_cache_manager
        log_test_result("H2: Importação do sistema de cache", True)
        
        # Testar criação de instância
        cache = get_cache_manager()
        log_test_result("H2: Criação de CacheManager", cache is not None)
        
        # Testar operações básicas de cache
        await cache.set("test_key", "test_value", ttl=60)
        cached_value = await cache.get("test_key")
        log_test_result("H2: Operações set/get", cached_value == "test_value")
        
        # Testar invalidação
        await cache.delete("test_key")
        deleted_value = await cache.get("test_key")
        log_test_result("H2: Invalidação de cache", deleted_value is None)
        
    except ImportError as e:
        log_test_result("H2: Sistema de cache", False, f"ImportError: {e}")
    except Exception as e:
        log_test_result("H2: Sistema de cache", False, f"Error: {e}")


async def validate_h3_gateway_system():
    """Valida Sistema H3 - API Gateway."""
    logger.info("🔍 Validando H3 - API Gateway...")
    
    try:
        # Testar importação do gateway
        from api.gateway import APIGateway, GatewayConfig, create_gateway
        log_test_result("H3: Importação do gateway", True)
        
        # Testar configuração
        config = GatewayConfig()
        log_test_result("H3: Criação de configuração", config is not None)
        
        # Testar criação do gateway
        gateway = APIGateway(config)
        log_test_result("H3: Criação do gateway", gateway is not None)
        
        # Testar inicialização
        await gateway.initialize()
        log_test_result("H3: Inicialização do gateway", gateway.is_initialized())
        
        # Testar obtenção da app FastAPI
        app = gateway.get_app()
        log_test_result("H3: Obtenção da aplicação FastAPI", app is not None)
        
    except ImportError as e:
        log_test_result("H3: Gateway", False, f"ImportError: {e}")
    except Exception as e:
        log_test_result("H3: Gateway", False, f"Error: {e}")


async def validate_h3_auth_system():
    """Valida Sistema H3 - Autenticação."""
    logger.info("🔍 Validando H3 - Sistema de Autenticação...")
    
    try:
        # Testar importação do sistema de auth
        from api.auth import AuthManager, UserManager, get_auth_manager
        log_test_result("H3: Importação do sistema de auth", True)
        
        # Testar criação de instância
        auth_manager = get_auth_manager()
        log_test_result("H3: Criação de AuthManager", auth_manager is not None)
        
        # Testar criação de usuário
        user_manager = UserManager()
        user = await user_manager.create_user(
            username="test_user",
            email="test@example.com", 
            password="test123",
            first_name="Test",
            last_name="User"
        )
        log_test_result("H3: Criação de usuário", user is not None)
        
        # Testar autenticação
        if user:
            auth_result = await auth_manager.authenticate_user("test_user", "test123")
            log_test_result("H3: Autenticação de usuário", auth_result.success)
        
    except ImportError as e:
        log_test_result("H3: Sistema de auth", False, f"ImportError: {e}")
    except Exception as e:
        log_test_result("H3: Sistema de auth", False, f"Error: {e}")


async def validate_h3_websocket_system():
    """Valida Sistema H3 - WebSocket."""
    logger.info("🔍 Validando H3 - Sistema WebSocket...")
    
    try:
        # Testar importação do sistema WebSocket
        from api.websocket import (
            ConnectionManager,
            MessageType,
            WSMessage,
            get_connection_manager,
        )
        log_test_result("H3: Importação do sistema WebSocket", True)
        
        # Testar criação de instância
        ws_manager = get_connection_manager()
        log_test_result("H3: Criação de ConnectionManager", ws_manager is not None)
        
        # Testar criação de mensagem
        message = WSMessage(type=MessageType.TEXT, data="test message")
        log_test_result("H3: Criação de WSMessage", message is not None)
        
        # Testar estatísticas
        stats = ws_manager.get_connection_stats()
        log_test_result("H3: Obtenção de estatísticas", isinstance(stats, dict))
        
    except ImportError as e:
        log_test_result("H3: Sistema WebSocket", False, f"ImportError: {e}")
    except Exception as e:
        log_test_result("H3: Sistema WebSocket", False, f"Error: {e}")


async def validate_middleware_integration():
    """Valida integração de middlewares."""
    logger.info("🔍 Validando Integração de Middlewares...")
    
    try:
        # Testar importação de middlewares
        from api.gateway.middleware import (
            AuthenticationMiddleware,
            LoggingMiddleware,
            RateLimitMiddleware,
            SecurityMiddleware,
            get_active_middlewares,
        )
        log_test_result("H3: Importação de middlewares", True)
        
        # Testar criação de middlewares
        from api.gateway.config import get_gateway_config
        config = get_gateway_config()
        
        logging_mw = LoggingMiddleware(config)
        security_mw = SecurityMiddleware(config)
        rate_limit_mw = RateLimitMiddleware(config)
        auth_mw = AuthenticationMiddleware(config)
        
        log_test_result("H3: Criação de middlewares", all([
            logging_mw is not None,
            security_mw is not None, 
            rate_limit_mw is not None,
            auth_mw is not None
        ]))
        
        # Testar obtenção de middlewares ativos
        active_middlewares = get_active_middlewares(config)
        log_test_result("H3: Middlewares ativos", isinstance(active_middlewares, list))
        
    except ImportError as e:
        log_test_result("H3: Middlewares", False, f"ImportError: {e}")
    except Exception as e:
        log_test_result("H3: Middlewares", False, f"Error: {e}")


async def validate_router_management():
    """Valida gerenciamento de rotas."""
    logger.info("🔍 Validando Gerenciamento de Rotas...")
    
    try:
        # Testar importação do router manager
        from api.gateway.router_manager import RouteMetadata, RouterManager
        log_test_result("H3: Importação do RouterManager", True)
        
        # Testar criação de instância
        router_manager = RouterManager()
        log_test_result("H3: Criação de RouterManager", router_manager is not None)
        
        # Testar listagem de routers
        routers = router_manager.list_routers()
        log_test_result("H3: Listagem de routers", isinstance(routers, list))
        
        # Testar criação de router unificado
        unified_router = router_manager.create_unified_router()
        log_test_result("H3: Router unificado", unified_router is not None)
        
    except ImportError as e:
        log_test_result("H3: RouterManager", False, f"ImportError: {e}")
    except Exception as e:
        log_test_result("H3: RouterManager", False, f"Error: {e}")


async def validate_configuration_system():
    """Valida sistema de configuração."""
    logger.info("🔍 Validando Sistema de Configuração...")
    
    try:
        # Testar configurações do gateway
        from api.gateway.config import GatewayConfig, SecurityLevel, get_gateway_config
        log_test_result("H3: Importação de configurações", True)
        
        # Testar criação de configuração
        config = GatewayConfig()
        log_test_result("H3: Criação de configuração", config is not None)
        
        # Testar configuração singleton
        config_singleton = get_gateway_config()
        log_test_result("H3: Configuração singleton", config_singleton is not None)
        
        # Testar geração de headers de segurança
        security_headers = config.get_security_headers()
        log_test_result("H3: Headers de segurança", isinstance(security_headers, dict))
        
        # Testar configuração CORS
        cors_origins = config.get_cors_origins()
        log_test_result("H3: Configuração CORS", isinstance(cors_origins, list))
        
    except ImportError as e:
        log_test_result("H3: Configurações", False, f"ImportError: {e}")
    except Exception as e:
        log_test_result("H3: Configurações", False, f"Error: {e}")


async def validate_complete_integration():
    """Valida integração completa do sistema."""
    logger.info("🔍 Validando Integração Completa...")
    
    try:
        # Testar criação de gateway completo
        from api.gateway import create_gateway, get_gateway_instance

        # Criar gateway
        gateway = await create_gateway()
        log_test_result("H3: Criação de gateway completo", gateway is not None)
        
        # Testar singleton
        gateway_singleton = await get_gateway_instance()
        log_test_result("H3: Gateway singleton", gateway_singleton is not None)
        
        # Testar obtenção de app configurada
        from api.gateway.gateway_main import get_configured_app
        app = await get_configured_app()
        log_test_result("H3: App configurada", app is not None)
        
    except ImportError as e:
        log_test_result("H3: Integração completa", False, f"ImportError: {e}")
    except Exception as e:
        log_test_result("H3: Integração completa", False, f"Error: {e}")


async def run_performance_tests():
    """Executa testes básicos de performance."""
    logger.info("🔍 Executando Testes de Performance...")
    
    try:
        import time

        # Teste de performance do cache
        from cache import get_cache_manager
        cache = get_cache_manager()
        
        start_time = time.time()
        for i in range(100):
            await cache.set(f"perf_key_{i}", f"value_{i}")
        cache_write_time = time.time() - start_time
        
        start_time = time.time()
        for i in range(100):
            await cache.get(f"perf_key_{i}")
        cache_read_time = time.time() - start_time
        
        log_test_result("H3: Performance de cache", 
                       cache_write_time < 1.0 and cache_read_time < 0.5,
                       f"Write: {cache_write_time:.3f}s, Read: {cache_read_time:.3f}s")
        
    except Exception as e:
        log_test_result("H3: Testes de performance", False, f"Error: {e}")


def print_validation_summary():
    """Imprime resumo da validação."""
    logger.info("\n" + "="*80)
    logger.info("📊 RESUMO DA VALIDAÇÃO DO SISTEMA H3")
    logger.info("="*80)
    
    total = validation_results["total_tests"]
    passed = validation_results["passed"]
    failed = validation_results["failed"]
    
    logger.info(f"Total de testes: {total}")
    logger.info(f"Testes aprovados: {passed}")
    logger.info(f"Testes falharam: {failed}")
    logger.info(f"Taxa de sucesso: {(passed/total*100):.1f}%" if total > 0 else "N/A")
    
    if failed > 0:
        logger.info("\n❌ ERROS ENCONTRADOS:")
        for error in validation_results["errors"]:
            logger.error(f"  - {error}")
    
    if passed == total:
        logger.info("\n🎉 TODOS OS TESTES PASSARAM! Sistema H3 validado com sucesso!")
        return True
    else:
        logger.info(f"\n⚠️  {failed} teste(s) falharam. Verifique os erros acima.")
        return False


async def main():
    """Função principal de validação."""
    logger.info("🚀 Iniciando Validação Completa do Sistema H3")
    logger.info("="*80)
    
    try:
        # Executar validações em sequência
        await validate_h1_monitoring_system()
        await validate_h2_cache_system() 
        await validate_h3_gateway_system()
        await validate_h3_auth_system()
        await validate_h3_websocket_system()
        await validate_middleware_integration()
        await validate_router_management()
        await validate_configuration_system()
        await validate_complete_integration()
        await run_performance_tests()
        
    except Exception as e:
        logger.error(f"Erro crítico durante validação: {e}")
        logger.error(traceback.format_exc())
        validation_results["errors"].append(f"Erro crítico: {e}")
    
    # Imprimir resumo
    success = print_validation_summary()
    
    # Retornar código de saída apropriado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())    success = print_validation_summary()
    
    # Retornar código de saída apropriado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())