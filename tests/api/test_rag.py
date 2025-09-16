"""Tests for RAG endpoints."""

from fastapi.testclient import TestClient


def test_rag_query_without_auth(client: TestClient):
    """Test RAG query endpoint returns 401 without API key."""
    response = client.post(
        "/rag/query",
        json={"query": "test query", "collection": "documents", "limit": 5},
    )
    assert response.status_code == 401


def test_rag_query_with_invalid_auth(
    client: TestClient, invalid_api_headers: dict[str, str]
):
    """Test RAG query endpoint returns 401 with invalid API key."""
    response = client.post(
        "/rag/query",
        json={"query": "test query", "collection": "documents", "limit": 5},
        headers=invalid_api_headers,
    )
    assert response.status_code == 401


def test_rag_query_with_valid_auth(client: TestClient, api_headers: dict[str, str]):
    """Test RAG query endpoint accepts valid requests."""
    response = client.post(
        "/rag/query",
        json={"query": "test query", "collection": "documents", "limit": 5},
        headers=api_headers,
    )

    # Should be 200 or 503 (if service unavailable)
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "metadata" in data


def test_rag_query_invalid_schema(client: TestClient, api_headers: dict[str, str]):
    """Test RAG query endpoint validates request schema."""
    response = client.post(
        "/rag/query", json={"invalid_field": "value"}, headers=api_headers
    )
    assert response.status_code == 422


def test_rag_health(client: TestClient):
    """Test RAG health endpoint."""
    response = client.get("/rag/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ["ready", "unavailable", "error"]
