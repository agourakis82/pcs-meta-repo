"""Test configuration and fixtures."""

import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI application."""
    # Set test environment variables
    os.environ["API_KEY"] = "test-api-key"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["RATE_LIMIT_REQUESTS"] = "100"
    os.environ["RATE_LIMIT_WINDOW"] = "60"
    
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def api_headers() -> dict[str, str]:
    """Headers with valid API key."""
    return {"x-api-key": "test-api-key"}


@pytest.fixture
def invalid_api_headers() -> dict[str, str]:
    """Headers with invalid API key."""
    return {"x-api-key": "invalid-key"}