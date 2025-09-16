"""
Testes de Integração - Sistema H2 (Cache)

Testes completos para validar o sistema de cache,
incluindo operações CRUD, performance e distribuição.
"""

import asyncio
import os
import sys
import time

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging

from tests.test_framework import TestSuite, test_framework

logger = logging.getLogger(__name__)


class H2IntegrationTests:
    """Testes de integração para o Sistema H2."""
    
    @staticmethod
    async def setup():
        """Setup inicial para testes H2."""
        logger.info("Configurando ambiente de testes H2")
    
    @staticmethod
    async def teardown():
        """Limpeza após testes H2."""
        logger.info("Limpando ambiente de testes H2")
    
    @staticmethod
    async def test_h2_cache_basic_operations():
        """Testa operações básicas do cache H2."""
        try:
            from api.cache.redis_cache import get_cache_client
            
            cache = get_cache_client()
            
            # Teste de SET
            test_key = "test_integration_h2"
            test_value = {"data": "test_value", "timestamp": time.time()}
            
            set_result = await cache.set(test_key, test_value, ttl=60)
            assert set_result, "Operação SET deve ser bem-sucedida"
            
            # Teste de GET
            retrieved_value = await cache.get(test_key)
            assert retrieved_value is not None, "Valor deve ser recuperado"
            assert retrieved_value["data"] == test_value["data"], "Dados devem coincidir"
            
            # Teste de DELETE
            delete_result = await cache.delete(test_key)
            assert delete_result, "Operação DELETE deve ser bem-sucedida"
            
            # Verificar se foi realmente deletado
            deleted_value = await cache.get(test_key)
            assert deleted_value is None, "Valor deve ter sido removido"
            
            return {
                "passed": True,
                "metrics": {
                    "set_success": set_result,
                    "get_success": retrieved_value is not None,
                    "delete_success": delete_result,
                    "data_integrity": retrieved_value["data"] == test_value["data"] if retrieved_value else False
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de cache não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h2_cache_performance():
        """Testa performance do cache H2."""
        try:
            from api.cache.redis_cache import get_cache_client
            
            cache = get_cache_client()
            
            # Teste de performance - múltiplas operações
            num_operations = 100
            test_data = {"large_data": "x" * 1000}  # 1KB de dados
            
            # Medir tempo de escritas
            start_time = time.time()
            for i in range(num_operations):
                await cache.set(f"perf_test_{i}", test_data, ttl=30)
            write_time = time.time() - start_time
            
            # Medir tempo de leituras
            start_time = time.time()
            for i in range(num_operations):
                await cache.get(f"perf_test_{i}")
            read_time = time.time() - start_time
            
            # Limpar dados de teste
            for i in range(num_operations):
                await cache.delete(f"perf_test_{i}")
            
            # Calcular métricas
            write_ops_per_sec = num_operations / write_time
            read_ops_per_sec = num_operations / read_time
            
            return {
                "passed": write_ops_per_sec > 10 and read_ops_per_sec > 10,  # Mínimo aceitável
                "metrics": {
                    "write_time": write_time,
                    "read_time": read_time,
                    "write_ops_per_sec": write_ops_per_sec,
                    "read_ops_per_sec": read_ops_per_sec,
                    "operations_tested": num_operations
                }
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h2_cache_ttl():
        """Testa TTL (Time To Live) do cache H2."""
        try:
            from api.cache.redis_cache import get_cache_client
            
            cache = get_cache_client()
            
            test_key = "ttl_test_h2"
            test_value = "expires_soon"
            ttl_seconds = 2
            
            # Define valor com TTL curto
            await cache.set(test_key, test_value, ttl=ttl_seconds)
            
            # Verifica se valor existe inicialmente
            initial_value = await cache.get(test_key)
            assert initial_value == test_value, "Valor deve existir inicialmente"
            
            # Aguarda TTL expirar
            await asyncio.sleep(ttl_seconds + 0.5)
            
            # Verifica se valor expirou
            expired_value = await cache.get(test_key)
            assert expired_value is None, "Valor deve ter expirado"
            
            return {
                "passed": True,
                "metrics": {
                    "ttl_tested": ttl_seconds,
                    "initial_retrieval": initial_value == test_value,
                    "expired_correctly": expired_value is None
                }
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h2_cache_patterns():
        """Testa padrões de cache (pattern matching)."""
        try:
            from api.cache.redis_cache import get_cache_client
            
            cache = get_cache_client()
            
            # Criar múltiplas chaves com padrão
            pattern_prefix = "pattern_test_h2"
            test_keys = [f"{pattern_prefix}:{i}" for i in range(5)]
            
            # Inserir dados
            for key in test_keys:
                await cache.set(key, f"value_for_{key}", ttl=60)
            
            # Testar busca por padrão
            found_keys = await cache.keys(f"{pattern_prefix}:*")
            
            # Limpar dados
            for key in test_keys:
                await cache.delete(key)
            
            return {
                "passed": len(found_keys) == len(test_keys),
                "metrics": {
                    "keys_created": len(test_keys),
                    "keys_found": len(found_keys),
                    "pattern_used": f"{pattern_prefix}:*"
                }
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h2_cache_serialization():
        """Testa serialização de diferentes tipos de dados."""
        try:
            from api.cache.redis_cache import get_cache_client
            
            cache = get_cache_client()
            
            # Testa diferentes tipos de dados
            test_cases = {
                "string": "test_string",
                "integer": 42,
                "float": 3.14159,
                "list": [1, 2, 3, "four"],
                "dict": {"nested": {"data": True}},
                "boolean": True,
                "none": None
            }
            
            serialization_results = {}
            
            for data_type, test_value in test_cases.items():
                key = f"serialization_test_{data_type}"
                
                # Set e Get
                await cache.set(key, test_value, ttl=60)
                retrieved = await cache.get(key)
                
                # Verifica integridade
                integrity_ok = retrieved == test_value
                serialization_results[data_type] = integrity_ok
                
                # Limpa
                await cache.delete(key)
            
            all_passed = all(serialization_results.values())
            
            return {
                "passed": all_passed,
                "metrics": {
                    "types_tested": len(test_cases),
                    "types_passed": sum(serialization_results.values()),
                    "results": serialization_results
                }
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h2_integration_with_other_systems():
        """Testa integração do H2 com outros sistemas."""
        try:
            # Testa se cache pode ser usado pelos outros sistemas
            from api.cache import get_cache_client
            
            cache = get_cache_client()
            
            # Simula uso por H1 (monitoring)
            h1_key = "h1:metrics:test"
            h1_data = {"cpu": 50, "memory": 75}
            await cache.set(h1_key, h1_data, ttl=300)
            h1_retrieved = await cache.get(h1_key)
            h1_integration = h1_retrieved == h1_data
            
            # Simula uso por H3 (APIs)
            h3_key = "h3:session:test"
            h3_data = {"user_id": 123, "session": "abc123"}
            await cache.set(h3_key, h3_data, ttl=3600)
            h3_retrieved = await cache.get(h3_key)
            h3_integration = h3_retrieved == h3_data
            
            # Simula uso por H4 (data processing)
            h4_key = "h4:pipeline:test"
            h4_data = {"pipeline_id": "test_pipeline", "status": "running"}
            await cache.set(h4_key, h4_data, ttl=1800)
            h4_retrieved = await cache.get(h4_key)
            h4_integration = h4_retrieved == h4_data
            
            # Limpa dados de teste
            await cache.delete(h1_key)
            await cache.delete(h3_key)
            await cache.delete(h4_key)
            
            integrations_working = sum([h1_integration, h3_integration, h4_integration])
            
            return {
                "passed": integrations_working == 3,
                "metrics": {
                    "h1_integration": h1_integration,
                    "h3_integration": h3_integration,
                    "h4_integration": h4_integration,
                    "total_integrations": integrations_working
                }
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }


# Registra a suite de testes H2
def register_h2_tests():
    """Registra todos os testes H2 no framework."""
    
    suite = TestSuite(
        name="h2_integration",
        description="Testes de integração do Sistema H2 (Cache)",
        setup_func=H2IntegrationTests.setup,
        teardown_func=H2IntegrationTests.teardown
    )
    
    # Adiciona todos os métodos de teste
    suite.tests = [
        H2IntegrationTests.test_h2_cache_basic_operations,
        H2IntegrationTests.test_h2_cache_performance,
        H2IntegrationTests.test_h2_cache_ttl,
        H2IntegrationTests.test_h2_cache_patterns,
        H2IntegrationTests.test_h2_cache_serialization,
        H2IntegrationTests.test_h2_integration_with_other_systems
    ]
    
    test_framework.register_suite(suite)
    logger.info("Testes H2 registrados no framework")


# Função para executar apenas testes H2
async def run_h2_tests():
    """Executa apenas os testes H2."""
    register_h2_tests()
    
    results = await test_framework.run_suite("h2_integration")
    
    print("=" * 60)
    print("RESULTADOS DOS TESTES H2 (CACHE)")
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
    # Executa testes H2 quando executado diretamente
    success = asyncio.run(run_h2_tests())
    exit(0 if success else 1)    exit(0 if success else 1)