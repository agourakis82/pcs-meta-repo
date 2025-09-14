"""Integration tests for API functionality."""

import time
from fastapi.testclient import TestClient


def test_rate_limiting(client: TestClient, api_headers: dict[str, str]):
    """Test rate limiting functionality."""
    # Make many requests quickly
    responses = []
    for _ in range(10):
        response = client.get("/admin/health", headers=api_headers)
        responses.append(response.status_code)
    
    # Most should succeed, but if rate limiting is strict, some might be 429
    success_codes = [code for code in responses if code == 200]
    assert len(success_codes) >= 5  # At least some should succeed


def test_cors_headers(client: TestClient):
    """Test CORS headers when enabled."""
    response = client.get("/admin/health")
    
    # CORS is disabled by default, so no CORS headers expected
    assert "access-control-allow-origin" not in response.headers


def test_openapi_schema(client: TestClient):
    """Test that OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "PCS‑HELIO MCP API"


def test_docs_endpoint(client: TestClient):
    """Test that docs endpoint is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_redoc_endpoint(client: TestClient):
    """Test that redoc endpoint is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_service_health_integration(client: TestClient):
    """Test that all services report health status."""
    response = client.get("/admin/health")
    assert response.status_code == 200
    
    data = response.json()
    services = data.get("services", {})
    
    # Check that key services are reported
    expected_services = [
        "rag_service", "ag5_service", "helio_service", "notebook_service"
    ]
    for service in expected_services:
        assert service in services
        assert services[service] in ["ready", "unavailable", "error"]


def test_error_handling(client: TestClient):
    """Test error handling for non-existent endpoints."""
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_method_not_allowed(client: TestClient):
    """Test method not allowed responses."""
    response = client.put("/admin/health")
    assert response.status_code == 405


def test_request_response_timing(client: TestClient):
    """Test that API responds within reasonable time."""
    start_time = time.time()
    response = client.get("/admin/health")
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 5.0  # Should respond within 5 seconds