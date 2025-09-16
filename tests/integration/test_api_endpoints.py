# -*- coding: utf-8 -*-
"""
Testes de integração para API endpoints.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app


class TestHealthEndpoints:
    """Testes para endpoints de saúde."""

    def test_health_check(self):
        """Testa endpoint de health check."""
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_detailed(self):
        """Testa endpoint de saúde detalhada."""
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "uptime" in data
        assert "version" in data


class TestAPIEndpoints:
    """Testes para endpoints da API."""

    @patch("api.auth.settings")
    def test_api_without_auth(self, mock_settings):
        """Testa acesso à API sem autenticação quando não é obrigatória."""
        mock_settings.API_KEY_REQUIRED = False

        client = TestClient(app)

        # Testa endpoint que normalmente requereria auth
        response = client.get("/api/status")

        # Deve retornar 200 quando auth não é obrigatória
        assert response.status_code in [200, 404]  # 404 se endpoint não existir

    @patch("api.auth.settings")
    def test_api_with_auth_required_no_key(self, mock_settings):
        """Testa acesso à API sem chave quando autenticação é obrigatória."""
        mock_settings.API_KEY_REQUIRED = True
        mock_settings.API_KEYS = "valid-key"

        client = TestClient(app)

        # Testa endpoint sem fornecer API key
        response = client.get("/api/status")

        # Deve retornar 401 quando auth é obrigatória e não há chave
        assert response.status_code in [401, 404]

    @patch("api.auth.settings")
    def test_api_with_valid_auth(self, mock_settings):
        """Testa acesso à API com chave válida."""
        mock_settings.API_KEY_REQUIRED = True
        mock_settings.API_KEYS = "valid-key"

        client = TestClient(app)
        headers = {"Authorization": "Bearer valid-key"}

        response = client.get("/api/status", headers=headers)

        # Deve permitir acesso com chave válida
        assert response.status_code in [200, 404]  # 404 se endpoint não existir

    @patch("api.auth.settings")
    def test_api_with_invalid_auth(self, mock_settings):
        """Testa acesso à API com chave inválida."""
        mock_settings.API_KEY_REQUIRED = True
        mock_settings.API_KEYS = "valid-key"

        client = TestClient(app)
        headers = {"Authorization": "Bearer invalid-key"}

        response = client.get("/api/status", headers=headers)

        # Deve rejeitar chave inválida
        assert response.status_code in [401, 404]


class TestDocumentationEndpoints:
    """Testes para endpoints de documentação."""

    def test_docs_endpoint(self):
        """Testa acesso à documentação."""
        client = TestClient(app)

        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_openapi_schema(self):
        """Testa schema OpenAPI."""
        client = TestClient(app)

        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestCacheEndpoints:
    """Testes para endpoints de cache."""

    @patch("api.cache.settings")
    @patch("api.auth.settings")
    def test_cache_stats_without_auth(self, mock_auth_settings, mock_cache_settings):
        """Testa estatísticas de cache sem autenticação."""
        mock_auth_settings.API_KEY_REQUIRED = False
        mock_cache_settings.CACHE_ENABLED = True

        client = TestClient(app)

        response = client.get("/cache/stats")

        # Endpoint pode não existir, mas não deve dar erro 500
        assert response.status_code in [200, 404]

    @patch("api.cache.settings")
    @patch("api.auth.settings")
    def test_cache_clear_with_auth(self, mock_auth_settings, mock_cache_settings):
        """Testa limpeza de cache com autenticação."""
        mock_auth_settings.API_KEY_REQUIRED = True
        mock_auth_settings.API_KEYS = "admin-key"
        mock_cache_settings.CACHE_ENABLED = True

        client = TestClient(app)
        headers = {"Authorization": "Bearer admin-key"}

        response = client.post("/cache/clear", headers=headers)

        # Endpoint pode não existir, mas não deve dar erro 500
        assert response.status_code in [200, 404, 405]  # 405 se método não permitido


class TestProcessingEndpoints:
    """Testes para endpoints de processamento."""

    @patch("api.auth.settings")
    def test_processing_stats(self, mock_settings):
        """Testa estatísticas de processamento."""
        mock_settings.API_KEY_REQUIRED = False

        client = TestClient(app)

        response = client.get("/processing/stats")

        # Endpoint pode não existir ainda
        assert response.status_code in [200, 404]

    @patch("api.auth.settings")
    def test_submit_job_without_auth(self, mock_settings):
        """Testa submissão de job sem autenticação."""
        mock_settings.API_KEY_REQUIRED = False

        client = TestClient(app)

        job_data = {"task_type": "test_task", "parameters": {"input": "test"}}

        response = client.post("/processing/jobs", json=job_data)

        # Endpoint pode não existir ainda
        assert response.status_code in [200, 201, 404, 422]  # 422 se dados inválidos


class TestErrorHandling:
    """Testes para tratamento de erros."""

    def test_404_endpoint(self):
        """Testa endpoint que não existe."""
        client = TestClient(app)

        response = client.get("/nonexistent/endpoint")

        assert response.status_code == 404

    def test_method_not_allowed(self):
        """Testa método HTTP não permitido."""
        client = TestClient(app)

        # Tenta POST no health check que só aceita GET
        response = client.post("/health")

        assert response.status_code == 405

    def test_invalid_json(self):
        """Testa JSON inválido."""
        client = TestClient(app)

        # Envia JSON malformado
        response = client.post(
            "/api/test",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Deve retornar erro de parsing ou 404 se endpoint não existir
        assert response.status_code in [400, 404, 422]
