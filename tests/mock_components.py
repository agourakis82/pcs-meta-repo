"""
Módulo de exemplo para demonstração dos testes.

Este módulo simula componentes básicos para mostrar
que o framework de testes está funcionando corretamente.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional


class MockHealthChecker:
    """Mock do sistema de health check."""

    async def check_system_health(self) -> Dict[str, Any]:
        """Simula verificação de saúde do sistema."""
        await asyncio.sleep(0.01)  # Simula processamento

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {"database": "healthy", "cache": "healthy", "api": "healthy"},
            "uptime": 3600,
            "memory_usage": 45.2,
        }


class MockCacheClient:
    """Mock do cliente de cache."""

    def __init__(self):
        self._data = {}

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Simula operação de set no cache."""
        await asyncio.sleep(0.001)  # Simula latência
        self._data[key] = {"value": value, "ttl": ttl, "timestamp": datetime.now()}
        return True

    async def get(self, key: str) -> Any:
        """Simula operação de get no cache."""
        await asyncio.sleep(0.001)  # Simula latência
        if key in self._data:
            return self._data[key]["value"]
        return None

    async def delete(self, key: str) -> bool:
        """Simula operação de delete no cache."""
        await asyncio.sleep(0.001)  # Simula latência
        if key in self._data:
            del self._data[key]
            return True
        return False


class MockAPIGateway:
    """Mock do API Gateway."""

    def __init__(self):
        self.routes = {
            ("GET", "/health"): self._health_endpoint,
            ("GET", "/api/v1/data"): self._data_endpoint,
            ("POST", "/api/v1/data"): self._create_endpoint,
        }

    async def handle_request(self, method: str, path: str) -> Dict[str, Any]:
        """Simula handling de requisição."""
        await asyncio.sleep(0.005)  # Simula processamento

        route_key = (method, path)
        if route_key in self.routes:
            handler = self.routes[route_key]
            return await handler()
        else:
            return {"status": 404, "error": "Endpoint not found"}

    async def find_route(self, method: str, path: str) -> Optional[Any]:
        """Simula busca de rota."""
        route_key = (method, path)
        return self.routes.get(route_key)

    async def _health_endpoint(self) -> Dict[str, Any]:
        """Endpoint de health."""
        return {
            "status": 200,
            "data": {"health": "ok", "timestamp": datetime.now().isoformat()},
        }

    async def _data_endpoint(self) -> Dict[str, Any]:
        """Endpoint de dados."""
        return {
            "status": 200,
            "data": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
        }

    async def _create_endpoint(self) -> Dict[str, Any]:
        """Endpoint de criação."""
        return {"status": 201, "data": {"id": 3, "name": "Item 3", "created": True}}


class MockDataProcessor:
    """Mock do processador de dados."""

    async def process_data(self, data: Any) -> Dict[str, Any]:
        """Simula processamento de dados."""
        await asyncio.sleep(0.01)  # Simula processamento

        if isinstance(data, dict):
            processed_count = len(data)
        elif isinstance(data, list):
            processed_count = len(data)
        else:
            processed_count = 1

        return {
            "processed": True,
            "input_type": type(data).__name__,
            "records_processed": processed_count,
            "processing_time": 0.01,
            "timestamp": datetime.now().isoformat(),
        }

    async def validate_data(self, data: Any) -> bool:
        """Simula validação de dados."""
        await asyncio.sleep(0.002)  # Simula validação

        # Considera válido se não for None ou vazio
        if data is None:
            return False
        if isinstance(data, (list, dict, str)) and len(data) == 0:
            return False

        return True


# Instâncias globais para uso nos testes
mock_health_checker = MockHealthChecker()
mock_cache_client = MockCacheClient()
mock_api_gateway = MockAPIGateway()
mock_data_processor = MockDataProcessor()


# Funções de conveniência para importação nos testes
def get_health_checker():
    """Retorna instância do health checker."""
    return mock_health_checker


def get_cache_client():
    """Retorna instância do cache client."""
    return mock_cache_client


def get_api_gateway():
    """Retorna instância do API gateway."""
    return mock_api_gateway


def get_data_processor():
    """Retorna instância do processador de dados."""
    return mock_data_processor
