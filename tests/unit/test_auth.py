# -*- coding: utf-8 -*-
"""
Testes unitários para o sistema de autenticação.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from starlette.datastructures import QueryParams

from api.auth import (
    extract_api_key,
    verify_api_key,
    require_api_key,
    AuthenticationError,
    InvalidAPIKeyError,
    MissingAPIKeyError,
    AuthMiddleware
)


class TestExtractApiKey:
    """Testes para extração de API key."""

    def test_extract_from_bearer_token(self):
        """Testa extração de API key do header Authorization."""
        request = MagicMock(spec=Request)
        request.headers = {"Authorization": "Bearer test-api-key"}
        request.query_params = QueryParams()
        
        api_key = extract_api_key(request)
        assert api_key == "test-api-key"

    def test_extract_from_query_param_api_key(self):
        """Testa extração de API key do parâmetro api_key."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.query_params = QueryParams("api_key=test-query-key")
        
        api_key = extract_api_key(request)
        assert api_key == "test-query-key"

    def test_extract_from_query_param_key(self):
        """Testa extração de API key do parâmetro key."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.query_params = QueryParams("key=test-short-key")
        
        api_key = extract_api_key(request)
        assert api_key == "test-short-key"

    def test_extract_priority_bearer_over_query(self):
        """Testa prioridade do Bearer token sobre query params."""
        request = MagicMock(spec=Request)
        request.headers = {"Authorization": "Bearer bearer-key"}
        request.query_params = QueryParams("api_key=query-key")
        
        api_key = extract_api_key(request)
        assert api_key == "bearer-key"

    def test_extract_no_api_key(self):
        """Testa quando não há API key."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.query_params = QueryParams()
        
        api_key = extract_api_key(request)
        assert api_key is None

    def test_extract_invalid_bearer_format(self):
        """Testa formato inválido de Bearer token."""
        request = MagicMock(spec=Request)
        request.headers = {"Authorization": "Basic invalid-format"}
        request.query_params = QueryParams()
        
        api_key = extract_api_key(request)
        assert api_key is None

    def test_extract_empty_bearer_token(self):
        """Testa Bearer token vazio."""
        request = MagicMock(spec=Request)
        request.headers = {"Authorization": "Bearer "}
        request.query_params = QueryParams()
        
        api_key = extract_api_key(request)
        assert api_key is None


class TestVerifyApiKey:
    """Testes para verificação de API key."""

    @patch('api.auth.settings')
    def test_verify_valid_api_key(self, mock_settings):
        """Testa verificação de API key válida."""
        mock_settings.API_KEYS = "key1,key2,key3"
        
        result = verify_api_key("key2")
        assert result is True

    @patch('api.auth.settings')
    def test_verify_invalid_api_key(self, mock_settings):
        """Testa verificação de API key inválida."""
        mock_settings.API_KEYS = "key1,key2,key3"
        
        result = verify_api_key("invalid-key")
        assert result is False

    @patch('api.auth.settings')
    def test_verify_empty_api_keys_config(self, mock_settings):
        """Testa verificação quando não há API keys configuradas."""
        mock_settings.API_KEYS = ""
        
        result = verify_api_key("any-key")
        assert result is False

    @patch('api.auth.settings')
    def test_verify_none_api_key(self, mock_settings):
        """Testa verificação com API key None."""
        mock_settings.API_KEYS = "key1,key2,key3"
        
        result = verify_api_key(None)
        assert result is False

    @patch('api.auth.settings')
    def test_verify_empty_api_key(self, mock_settings):
        """Testa verificação com API key vazia."""
        mock_settings.API_KEYS = "key1,key2,key3"
        
        result = verify_api_key("")
        assert result is False


class TestRequireApiKey:
    """Testes para o decorador require_api_key."""

    @pytest.mark.asyncio
    @patch('api.auth.settings')
    async def test_require_api_key_disabled(self, mock_settings):
        """Testa quando API key não é obrigatória."""
        mock_settings.API_KEY_REQUIRED = False
        
        @require_api_key
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        request = MagicMock(spec=Request)
        result = await test_endpoint(request)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    @patch('api.auth.settings')
    @patch('api.auth.extract_api_key')
    @patch('api.auth.verify_api_key')
    async def test_require_api_key_valid(self, mock_verify, mock_extract, mock_settings):
        """Testa com API key válida."""
        mock_settings.API_KEY_REQUIRED = True
        mock_extract.return_value = "valid-key"
        mock_verify.return_value = True
        
        @require_api_key
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        request = MagicMock(spec=Request)
        result = await test_endpoint(request)
        assert result == {"message": "success"}

    @pytest.mark.asyncio
    @patch('api.auth.settings')
    @patch('api.auth.extract_api_key')
    async def test_require_api_key_missing(self, mock_extract, mock_settings):
        """Testa com API key ausente."""
        mock_settings.API_KEY_REQUIRED = True
        mock_extract.return_value = None
        
        @require_api_key
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        request = MagicMock(spec=Request)
        
        with pytest.raises(MissingAPIKeyError):
            await test_endpoint(request)

    @pytest.mark.asyncio
    @patch('api.auth.settings')
    @patch('api.auth.extract_api_key')
    @patch('api.auth.verify_api_key')
    async def test_require_api_key_invalid(self, mock_verify, mock_extract, mock_settings):
        """Testa com API key inválida."""
        mock_settings.API_KEY_REQUIRED = True
        mock_extract.return_value = "invalid-key"
        mock_verify.return_value = False
        
        @require_api_key
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        request = MagicMock(spec=Request)
        
        with pytest.raises(InvalidAPIKeyError):
            await test_endpoint(request)


class TestAuthenticationErrors:
    """Testes para exceções de autenticação."""

    def test_authentication_error_default(self):
        """Testa AuthenticationError com valores padrão."""
        error = AuthenticationError()
        assert error.status_code == 401
        assert error.detail == "Authentication required"
        assert error.headers == {"WWW-Authenticate": "Bearer"}

    def test_authentication_error_custom_detail(self):
        """Testa AuthenticationError com detalhe customizado."""
        error = AuthenticationError("Custom auth error")
        assert error.status_code == 401
        assert error.detail == "Custom auth error"
        assert error.headers == {"WWW-Authenticate": "Bearer"}

    def test_invalid_api_key_error(self):
        """Testa InvalidAPIKeyError."""
        error = InvalidAPIKeyError()
        assert error.status_code == 401
        assert error.detail == "Invalid API key"
        assert error.headers == {"WWW-Authenticate": "Bearer"}

    def test_missing_api_key_error(self):
        """Testa MissingAPIKeyError."""
        error = MissingAPIKeyError()
        assert error.status_code == 401
        assert error.detail == "API key required"
        assert error.headers == {"WWW-Authenticate": "Bearer"}


class TestAuthMiddleware:
    """Testes para middleware de autenticação."""

    @patch('api.auth.settings')
    async def test_middleware_api_key_not_required(self, mock_settings):
        """Testa middleware quando API key não é obrigatória."""
        mock_settings.API_KEY_REQUIRED = False
        
        app = MagicMock()
        middleware = AuthMiddleware(app)
        
        scope = {"type": "http", "path": "/test"}
        receive = MagicMock()
        send = MagicMock()
        
        # Mock da aplicação
        async def mock_app(scope, receive, send):
            response = MagicMock()
            response.status_code = 200
            await send({"type": "http.response.start", "status": 200})
            await send({"type": "http.response.body", "body": b"OK"})
        
        app.side_effect = mock_app
        
        await middleware(scope, receive, send)
        app.assert_called_once_with(scope, receive, send)

    def test_middleware_excludes_health_check(self):
        """Testa se middleware exclui health check paths."""
        app = MagicMock()
        middleware = AuthMiddleware(app)
        
        # Health check paths devem ser excluídos
        assert middleware._should_authenticate("/") is False
        assert middleware._should_authenticate("/health") is False
        assert middleware._should_authenticate("/docs") is False
        assert middleware._should_authenticate("/openapi.json") is False
        
        # Outros paths devem requerer autenticação
        assert middleware._should_authenticate("/api/test") is True
        assert middleware._should_authenticate("/processing/jobs") is True