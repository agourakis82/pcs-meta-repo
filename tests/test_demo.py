"""
Teste de Demonstração

Este teste usa os mocks para demonstrar que o framework
de testes está funcionando corretamente.
"""

import asyncio
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import logging

from tests.mock_components import (
    get_api_gateway,
    get_cache_client,
    get_data_processor,
    get_health_checker,
)
from tests.test_framework import TestSuite, test_framework

logger = logging.getLogger(__name__)


class DemoTests:
    """Testes de demonstração."""
    
    @staticmethod
    async def setup():
        """Setup para testes demo."""
        logger.info("Configurando testes de demonstração")
        return True
    
    @staticmethod
    async def teardown():
        """Limpeza após testes demo."""
        logger.info("Limpando testes de demonstração")
        return True
    
    @staticmethod
    async def test_demo_health_check():
        """Demonstra teste de health check."""
        try:
            health_checker = get_health_checker()
            health_status = await health_checker.check_system_health()
            
            # Verifica se tem os campos esperados
            has_status = "status" in health_status
            has_components = "components" in health_status
            is_healthy = health_status.get("status") == "healthy"
            
            return {
                "passed": has_status and has_components and is_healthy,
                "metrics": {
                    "has_status": has_status,
                    "has_components": has_components,
                    "is_healthy": is_healthy,
                    "component_count": len(health_status.get("components", {}))
                }
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_demo_cache_operations():
        """Demonstra teste de operações de cache."""
        try:
            cache = get_cache_client()
            
            # Testa set
            set_result = await cache.set("test_key", "test_value")
            
            # Testa get
            get_result = await cache.get("test_key")
            
            # Testa delete
            delete_result = await cache.delete("test_key")
            
            # Verifica se não existe mais
            not_found = await cache.get("test_key")
            
            operations_successful = (
                set_result and 
                get_result == "test_value" and 
                delete_result and 
                not_found is None
            )
            
            return {
                "passed": operations_successful,
                "metrics": {
                    "set_success": set_result,
                    "get_success": get_result == "test_value",
                    "delete_success": delete_result,
                    "cleanup_success": not_found is None
                }
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_demo_api_requests():
        """Demonstra teste de requisições API."""
        try:
            gateway = get_api_gateway()
            
            # Testa endpoint de health
            health_response = await gateway.handle_request("GET", "/health")
            health_ok = health_response.get("status") == 200
            
            # Testa endpoint de dados
            data_response = await gateway.handle_request("GET", "/api/v1/data")
            data_ok = data_response.get("status") == 200
            
            # Testa endpoint inexistente
            not_found_response = await gateway.handle_request("GET", "/invalid")
            not_found_ok = not_found_response.get("status") == 404
            
            all_api_tests_passed = health_ok and data_ok and not_found_ok
            
            return {
                "passed": all_api_tests_passed,
                "metrics": {
                    "health_endpoint": health_ok,
                    "data_endpoint": data_ok,
                    "not_found_handling": not_found_ok,
                    "total_requests": 3
                }
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_demo_data_processing():
        """Demonstra teste de processamento de dados."""
        try:
            processor = get_data_processor()
            
            # Testa processamento de dict
            dict_data = {"key1": "value1", "key2": "value2"}
            dict_result = await processor.process_data(dict_data)
            dict_valid = await processor.validate_data(dict_data)
            
            # Testa processamento de lista
            list_data = [1, 2, 3, 4, 5]
            list_result = await processor.process_data(list_data)
            list_valid = await processor.validate_data(list_data)
            
            # Verifica resultados
            dict_processed = dict_result.get("processed", False)
            list_processed = list_result.get("processed", False)
            
            all_processing_successful = (
                dict_processed and dict_valid and
                list_processed and list_valid
            )
            
            return {
                "passed": all_processing_successful,
                "metrics": {
                    "dict_processing": dict_processed,
                    "dict_validation": dict_valid,
                    "list_processing": list_processed,
                    "list_validation": list_valid,
                    "dict_records": dict_result.get("records_processed", 0),
                    "list_records": list_result.get("records_processed", 0)
                }
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_demo_integration():
        """Demonstra teste de integração entre componentes."""
        try:
            # Usa múltiplos componentes juntos
            cache = get_cache_client()
            processor = get_data_processor()
            api = get_api_gateway()
            
            # Fluxo: API -> Cache -> Processamento
            api_response = await api.handle_request("GET", "/api/v1/data")
            
            if api_response.get("status") == 200:
                data = api_response.get("data", [])
                
                # Armazena no cache
                cache_stored = await cache.set("api_data", data)
                
                # Recupera do cache
                cached_data = await cache.get("api_data")
                
                # Processa os dados
                processing_result = await processor.process_data(cached_data)
                
                # Verifica se todo o fluxo funcionou
                integration_successful = (
                    cache_stored and
                    cached_data is not None and
                    processing_result.get("processed", False)
                )
                
                return {
                    "passed": integration_successful,
                    "metrics": {
                        "api_call": api_response.get("status") == 200,
                        "cache_storage": cache_stored,
                        "cache_retrieval": cached_data is not None,
                        "data_processing": processing_result.get("processed", False),
                        "records_in_flow": processing_result.get("records_processed", 0)
                    }
                }
            else:
                return {
                    "passed": False,
                    "error": "API call failed"
                }
                
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }


def register_demo_tests():
    """Registra testes de demonstração."""
    suite = TestSuite(
        name="demo_tests",
        description="Testes de Demonstração do Framework",
        setup_func=DemoTests.setup,
        teardown_func=DemoTests.teardown
    )
    
    suite.tests = [
        DemoTests.test_demo_health_check,
        DemoTests.test_demo_cache_operations,
        DemoTests.test_demo_api_requests,
        DemoTests.test_demo_data_processing,
        DemoTests.test_demo_integration
    ]
    
    test_framework.register_suite(suite)
    logger.info("Testes de demonstração registrados")


async def run_demo_tests():
    """Executa apenas os testes de demonstração."""
    register_demo_tests()
    
    results = await test_framework.run_suite("demo_tests")
    
    print("=" * 60)
    print("🎯 DEMONSTRAÇÃO DO FRAMEWORK DE TESTES")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"Testes executados: {total}")
    print(f"Testes passaram: {passed}")
    print(f"Taxa de sucesso: {(passed/total*100):.1f}%")
    
    for result in results:
        status = "✅" if result.passed else "❌"
        print(f"\n{status} {result.test_name} ({result.duration:.3f}s)")
        
        if result.metrics:
            print("   Métricas:")
            for key, value in result.metrics.items():
                print(f"     {key}: {value}")
        
        if not result.passed:
            print(f"   Erro: {result.error_message}")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_demo_tests())
    exit(0 if success else 1)if __name__ == "__main__":
    success = asyncio.run(run_demo_tests())
    exit(0 if success else 1)