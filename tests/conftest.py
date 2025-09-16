# -*- coding: utf-8 -*-
"""
Configuração pytest para testes do MCP Server PCS
================================================

Configurações globais e fixtures compartilhadas para todos os testes.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, AsyncGenerator, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Adiciona src ao path para importações
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from api.cache import CacheManager
from api.config import Settings

# Importações do sistema (usando nomes corretos das classes)
from api.main import app
from api.processing import JobManager


@pytest.fixture(scope="session")
def event_loop():
    """Cria um loop de eventos para testes assíncronos."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Cria um diretório temporário para testes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_config(temp_dir: Path) -> Settings:
    """Configuração de teste isolada."""
    config = Settings()
    # Sobrescreve configurações para teste
    config.ENV = "testing"
    config.API_KEY_REQUIRED = False
    config.API_KEYS = "test-api-key"
    config.RATE_LIMIT_REQUESTS_PER_MINUTE = 1000
    config.REDIS_URL = "redis://localhost:6379/15"  # DB de teste
    config.CACHE_ENABLED = True
    return config


@pytest.fixture
def mock_auth_manager():
    """Mock do sistema de autenticação para testes."""
    auth_manager = MagicMock()
    auth_manager.verify_api_key = AsyncMock(return_value=True)
    auth_manager.create_access_token = MagicMock(return_value="test-token")
    auth_manager.verify_token = AsyncMock(return_value={"sub": "test-user"})
    auth_manager.hash_password = MagicMock(return_value="hashed-password")
    auth_manager.verify_password = MagicMock(return_value=True)
    return auth_manager


@pytest.fixture
def mock_cache_manager():
    """Mock do CacheManager para testes."""
    cache_manager = MagicMock(spec=CacheManager)
    cache_manager.get = AsyncMock(return_value=None)
    cache_manager.set = AsyncMock(return_value=True)
    cache_manager.delete = AsyncMock(return_value=True)
    cache_manager.exists = AsyncMock(return_value=False)
    cache_manager.clear = AsyncMock(return_value=True)
    cache_manager.keys = AsyncMock(return_value=[])
    cache_manager.ttl = AsyncMock(return_value=-1)
    cache_manager.get_stats = AsyncMock(
        return_value={"hits": 0, "misses": 0, "keys": 0, "memory_usage": "0B"}
    )
    return cache_manager


@pytest.fixture
def mock_job_manager():
    """Mock do JobManager para testes."""
    job_manager = MagicMock(spec=JobManager)
    job_manager.submit_job = AsyncMock(return_value="test-job-id")
    job_manager.get_job_status = AsyncMock(
        return_value={
            "id": "test-job-id",
            "status": "completed",
            "result": {"message": "Test job completed"},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:01:00Z",
        }
    )
    job_manager.cancel_job = AsyncMock(return_value=True)
    job_manager.get_statistics = AsyncMock(
        return_value={
            "total_jobs": 1,
            "completed_jobs": 1,
            "failed_jobs": 0,
            "pending_jobs": 0,
            "active_workers": 2,
        }
    )
    job_manager.get_queue_status = AsyncMock(
        return_value={"queue_size": 0, "processing": 0, "average_wait_time": 0.0}
    )
    return job_manager


@pytest.fixture
def client():
    """Cliente de teste FastAPI."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Cliente assíncrono para testes."""
    async with AsyncClient(base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Headers de autenticação para testes."""
    return {"Authorization": "Bearer test-token", "X-API-Key": "test-api-key"}


@pytest.fixture
def sample_job_data() -> Dict[str, Any]:
    """Dados de exemplo para testes de jobs."""
    return {
        "task_type": "test_task",
        "parameters": {"input_data": "test data", "processing_mode": "standard"},
        "priority": 1,
        "metadata": {
            "user_id": "test-user",
            "description": "Test job for unit testing",
        },
    }


@pytest.fixture
def sample_user_data() -> Dict[str, str]:
    """Dados de usuário para testes."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def mock_database():
    """Mock de database para testes."""
    db_mock = MagicMock()
    db_mock.execute = AsyncMock()
    db_mock.fetch_one = AsyncMock()
    db_mock.fetch_all = AsyncMock(return_value=[])
    db_mock.commit = AsyncMock()
    db_mock.rollback = AsyncMock()
    return db_mock


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singletons entre testes."""
    # Reset de instâncias singleton se necessário
    yield
    # Cleanup após teste


# Configurações pytest
def pytest_configure(config: Any) -> None:
    """Configuração do pytest."""
    config.addinivalue_line("markers", "unit: marca testes unitários")
    config.addinivalue_line("markers", "integration: marca testes de integração")
    config.addinivalue_line("markers", "slow: marca testes que demoram para executar")
    config.addinivalue_line(
        "markers", "external: marca testes que dependem de serviços externos"
    )


def pytest_collection_modifyitems(config: Any, items: Any) -> None:
    """Modifica a coleta de testes."""
    for item in items:
        # Adiciona marcadores baseados no path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Adiciona marcador slow para testes com async
        if "async" in item.name or hasattr(item, "pytestmark"):
            for mark in getattr(item, "pytestmark", []):
                if mark.name == "asyncio":
                    item.add_marker(pytest.mark.slow)
                    item.add_marker(pytest.mark.slow)
