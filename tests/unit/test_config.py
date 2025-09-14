# -*- coding: utf-8 -*-
"""
Testes unitários para o sistema de configuração.
"""

import pytest
from api.config import Settings


class TestSettings:
    """Testes para a classe Settings."""

    def test_settings_default_values(self):
        """Testa valores padrão das configurações."""
        settings = Settings()
        
        assert settings.API_NAME == "PCS‑HELIO MCP API"
        assert settings.ENV == "development"
        assert settings.API_KEY_REQUIRED is False
        assert settings.RATE_LIMIT_REQUESTS_PER_MINUTE == 60
        assert settings.CACHE_ENABLED is True
        assert settings.CACHE_DEFAULT_TTL == 3600

    def test_settings_custom_values(self):
        """Testa configurações customizadas."""
        settings = Settings(
            API_NAME="Test API",
            ENV="testing",
            API_KEY_REQUIRED=True,
            RATE_LIMIT_REQUESTS_PER_MINUTE=120
        )
        
        assert settings.API_NAME == "Test API"
        assert settings.ENV == "testing"
        assert settings.API_KEY_REQUIRED is True
        assert settings.RATE_LIMIT_REQUESTS_PER_MINUTE == 120

    def test_api_keys_parsing_string(self):
        """Testa parsing de API keys como string."""
        settings = Settings(API_KEYS="key1,key2,key3")
        assert settings.API_KEYS == "key1,key2,key3"

    def test_api_keys_parsing_list(self):
        """Testa parsing de API keys como lista."""
        # Simula o comportamento do validator
        from api.config import Settings
        result = Settings.parse_api_keys(["key1", "key2", "key3"])
        assert result == "key1,key2,key3"

    def test_api_keys_parsing_empty(self):
        """Testa parsing de API keys vazias."""
        from api.config import Settings
        result = Settings.parse_api_keys("")
        assert result == ""
        
        result = Settings.parse_api_keys(None)
        assert result == ""

    @pytest.mark.parametrize("env,expected", [
        ("development", "development"),
        ("production", "production"),
        ("testing", "testing"),
        ("DEVELOPMENT", "DEVELOPMENT"),  # Case sensitive
    ])
    def test_environment_values(self, env: str, expected: str):
        """Testa diferentes valores de ambiente."""
        settings = Settings(ENV=env)
        assert settings.ENV == expected

    def test_data_paths_defaults(self):
        """Testa paths padrão de dados."""
        settings = Settings()
        
        assert settings.DATA_DIR == "./data"
        assert settings.NOTEBOOK_DIR == "./notebooks"
        assert settings.REPORTS_DIR == "./reports"
        assert settings.CHROMA_PATH == "./ragpp/index/lit2025"

    def test_cache_configuration(self):
        """Testa configurações de cache."""
        settings = Settings(
            CACHE_ENABLED=False,
            CACHE_MEMORY_SIZE=2000,
            CACHE_DEFAULT_TTL=7200,
            REDIS_URL="redis://localhost:6380/1"
        )
        
        assert settings.CACHE_ENABLED is False
        assert settings.CACHE_MEMORY_SIZE == 2000
        assert settings.CACHE_DEFAULT_TTL == 7200
        assert settings.REDIS_URL == "redis://localhost:6380/1"

    def test_rate_limiting_configuration(self):
        """Testa configurações de rate limiting."""
        settings = Settings(
            RATE_LIMIT_REQUESTS_PER_MINUTE=100,
            RATE_LIMIT_BURST_CAPACITY=20,
            RATE_LIMIT_REFILL_RATE=2.0
        )
        
        assert settings.RATE_LIMIT_REQUESTS_PER_MINUTE == 100
        assert settings.RATE_LIMIT_BURST_CAPACITY == 20
        assert settings.RATE_LIMIT_REFILL_RATE == 2.0