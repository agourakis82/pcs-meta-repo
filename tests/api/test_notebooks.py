"""Tests for notebook endpoints."""

from fastapi.testclient import TestClient


def test_list_notebooks_without_auth(client: TestClient):
    """Test listing notebooks without auth (should work with optional auth)."""
    response = client.get("/notebooks/")
    assert response.status_code == 200

    data = response.json()
    assert "notebooks" in data
    assert isinstance(data["notebooks"], list)


def test_list_notebooks_with_auth(client: TestClient, api_headers: dict[str, str]):
    """Test listing notebooks with valid auth."""
    response = client.get("/notebooks/", headers=api_headers)
    assert response.status_code == 200

    data = response.json()
    assert "notebooks" in data
    assert isinstance(data["notebooks"], list)


def test_list_notebooks_with_invalid_auth(
    client: TestClient, invalid_api_headers: dict[str, str]
):
    """Test listing notebooks with invalid auth (should return 401)."""
    response = client.get("/notebooks/", headers=invalid_api_headers)
    assert response.status_code == 401


def test_notebooks_health(client: TestClient):
    """Test notebooks health endpoint."""
    response = client.get("/notebooks/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ["ready", "unavailable", "error"]
