"""Tests for admin endpoints."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test the health endpoint returns 200 and proper structure."""
    response = client.get("/admin/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "uptime_s" in data
    assert "services" in data
    assert isinstance(data["uptime_s"], (int, float))
    assert data["uptime_s"] >= 0


def test_version_endpoint(client: TestClient):
    """Test the version endpoint returns 200 and proper structure."""
    response = client.get("/admin/version")
    assert response.status_code == 200

    data = response.json()
    assert "api_version" in data
    assert "git_sha" in data
    assert "package_version" in data
    assert isinstance(data["api_version"], str)


def test_root_endpoint(client: TestClient):
    """Test the root endpoint returns basic API info."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs_url" in data
    assert data["docs_url"] == "/docs"


def test_root_health_endpoint(client: TestClient):
    """Test the root health endpoint returns simple status."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert data["status"] in ["ok", "error"]
