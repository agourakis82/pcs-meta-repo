"""
Testes de Integração - Sistema H3 (APIs)

Testes completos para validar o sistema de APIs,
incluindo endpoints, autenticação, middleware e gateway.
"""

import asyncio
import json
import os
import sys

import aiohttp

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging

from tests.test_framework import TestSuite, test_framework

logger = logging.getLogger(__name__)


class H3IntegrationTests:
    """Testes de integração para o Sistema H3."""
    
    @staticmethod
    async def setup():
        """Setup inicial para testes H3."""
        logger.info("Configurando ambiente de testes H3")
        # Pode incluir inicialização de servidor de testes
    
    @staticmethod
    async def teardown():
        """Limpeza após testes H3."""
        logger.info("Limpando ambiente de testes H3")
    
    @staticmethod
    async def test_h3_health_endpoint():
        """Testa endpoint de health do H3."""
        try:
            from api.gateway.health import get_health_status

            # Testa health check direto (sem HTTP)
            health_status = await get_health_status()
            
            assert isinstance(health_status, dict), "Health status deve ser um dicionário"
            assert "status" in health_status, "Deve conter campo status"
            assert "timestamp" in health_status, "Deve conter timestamp"
            
            # Verifica se status é válido
            valid_statuses = ["healthy", "degraded", "unhealthy"]
            status_valid = health_status.get("status") in valid_statuses
            
            return {
                "passed": status_valid,
                "metrics": {
                    "status": health_status.get("status"),
                    "components": len(health_status.get("components", {})),
                    "has_timestamp": "timestamp" in health_status
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
    async def test_h3_middleware_pipeline():
        """Testa pipeline de middleware do H3."""
        try:
            from api.gateway.middleware import MiddlewarePipeline
            
            pipeline = MiddlewarePipeline()
            
            # Simula request/response
            test_request = {
                "method": "GET",
                "path": "/test",
                "headers": {"user-agent": "test"},
                "body": None
            }
            
            test_response = {
                "status": 200,
                "headers": {"content-type": "application/json"},
                "body": {"message": "test"}
            }
            
            # Processa através do pipeline
            processed_request = await pipeline.process_request(test_request)
            processed_response = await pipeline.process_response(test_response)
            
            # Verifica se processamento foi bem-sucedido
            request_processed = processed_request is not None
            response_processed = processed_response is not None
            
            return {
                "passed": request_processed and response_processed,
                "metrics": {
                    "request_processed": request_processed,
                    "response_processed": response_processed,
                    "middleware_count": len(pipeline.middlewares) if hasattr(pipeline, 'middlewares') else 0
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de middleware não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h3_authentication():
        """Testa sistema de autenticação do H3."""
        try:
            from api.gateway.auth import TokenManager
            
            token_manager = TokenManager()
            
            # Testa geração de token
            test_payload = {"user_id": 123, "role": "test"}
            token = await token_manager.create_token(test_payload)
            
            assert token is not None, "Token deve ser gerado"
            assert isinstance(token, str), "Token deve ser string"
            
            # Testa validação de token
            decoded_payload = await token_manager.validate_token(token)
            
            assert decoded_payload is not None, "Payload deve ser decodificado"
            assert decoded_payload.get("user_id") == 123, "User ID deve coincidir"
            
            return {
                "passed": True,
                "metrics": {
                    "token_generated": token is not None,
                    "token_validated": decoded_payload is not None,
                    "payload_integrity": decoded_payload.get("user_id") == 123
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de autenticação não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h3_rate_limiting():
        """Testa rate limiting do H3."""
        try:
            from api.gateway.rate_limit import RateLimiter
            
            rate_limiter = RateLimiter(max_requests=5, window_seconds=60)
            
            client_id = "test_client"
            requests_allowed = 0
            requests_denied = 0
            
            # Testa múltiplas requisições
            for i in range(10):  # Tenta 10 requisições (limite é 5)
                allowed = await rate_limiter.is_allowed(client_id)
                if allowed:
                    requests_allowed += 1
                else:
                    requests_denied += 1
            
            # Deve permitir 5 e negar 5
            rate_limiting_working = requests_allowed == 5 and requests_denied == 5
            
            return {
                "passed": rate_limiting_working,
                "metrics": {
                    "requests_allowed": requests_allowed,
                    "requests_denied": requests_denied,
                    "rate_limit": 5,
                    "total_requests": 10
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de rate limiting não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h3_api_gateway():
        """Testa funcionalidade do API Gateway."""
        try:
            from api.gateway.gateway import APIGateway
            
            gateway = APIGateway()
            
            # Testa roteamento
            test_routes = [
                {"method": "GET", "path": "/health", "expected": True},
                {"method": "POST", "path": "/api/v1/test", "expected": True},
                {"method": "GET", "path": "/invalid/path", "expected": False}
            ]
            
            routing_results = []
            
            for route in test_routes:
                try:
                    route_found = await gateway.find_route(route["method"], route["path"])
                    result = (route_found is not None) == route["expected"]
                    routing_results.append(result)
                except:
                    routing_results.append(False)
            
            all_routing_correct = all(routing_results)
            
            return {
                "passed": all_routing_correct,
                "metrics": {
                    "routes_tested": len(test_routes),
                    "routing_correct": sum(routing_results),
                    "gateway_functional": all_routing_correct
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de gateway não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h3_integration_with_other_systems():
        """Testa integração do H3 com outros sistemas."""
        try:
            # Testa se H3 pode acessar H1 (monitoring)
            h1_integration = False
            try:
                from api.monitoring import get_monitor
                monitor = get_monitor()
                h1_integration = monitor is not None
            except:
                pass
            
            # Testa se H3 pode acessar H2 (cache)
            h2_integration = False
            try:
                from api.cache import get_cache_client
                cache = get_cache_client()
                h2_integration = cache is not None
            except:
                pass
            
            # Testa se H3 pode acessar H4 (data processing)
            h4_integration = False
            try:
                from api.data_processing import system_info
                info = system_info()
                h4_integration = info is not None
            except:
                pass
            
            total_integrations = sum([h1_integration, h2_integration, h4_integration])
            
            return {
                "passed": total_integrations >= 2,  # Pelo menos 2 integrações funcionando
                "metrics": {
                    "h1_integration": h1_integration,
                    "h2_integration": h2_integration,
                    "h4_integration": h4_integration,
                    "total_integrations": total_integrations
                }
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h3_cors_handling():
        """Testa handling de CORS do H3."""
        try:
            from api.gateway.cors import CORSHandler
            
            cors_handler = CORSHandler()
            
            # Testa CORS preflight
            preflight_request = {
                "method": "OPTIONS",
                "headers": {
                    "origin": "http://localhost:3000",
                    "access-control-request-method": "POST",
                    "access-control-request-headers": "content-type"
                }
            }
            
            cors_response = await cors_handler.handle_preflight(preflight_request)
            
            # Verifica headers CORS
            has_cors_headers = all([
                "access-control-allow-origin" in cors_response.get("headers", {}),
                "access-control-allow-methods" in cors_response.get("headers", {}),
                "access-control-allow-headers" in cors_response.get("headers", {})
            ])
            
            return {
                "passed": has_cors_headers,
                "metrics": {
                    "preflight_handled": cors_response is not None,
                    "cors_headers_present": has_cors_headers,
                    "status_code": cors_response.get("status", 0)
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de CORS não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }


# Registra a suite de testes H3
def register_h3_tests():
    """Registra todos os testes H3 no framework."""
    
    suite = TestSuite(
        name="h3_integration",
        description="Testes de integração do Sistema H3 (APIs)",
        setup_func=H3IntegrationTests.setup,
        teardown_func=H3IntegrationTests.teardown
    )
    
    # Adiciona todos os métodos de teste
    suite.tests = [
        H3IntegrationTests.test_h3_health_endpoint,
        H3IntegrationTests.test_h3_middleware_pipeline,
        H3IntegrationTests.test_h3_authentication,
        H3IntegrationTests.test_h3_rate_limiting,
        H3IntegrationTests.test_h3_api_gateway,
        H3IntegrationTests.test_h3_integration_with_other_systems,
        H3IntegrationTests.test_h3_cors_handling
    ]
    
    test_framework.register_suite(suite)
    logger.info("Testes H3 registrados no framework")


# Função para executar apenas testes H3
async def run_h3_tests():
    """Executa apenas os testes H3."""
    register_h3_tests()
    
    results = await test_framework.run_suite("h3_integration")
    
    print("=" * 60)
    print("RESULTADOS DOS TESTES H3 (APIs)")
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
    # Executa testes H3 quando executado diretamente
    success = asyncio.run(run_h3_tests())
    exit(0 if success else 1)    success = asyncio.run(run_h3_tests())
    exit(0 if success else 1)