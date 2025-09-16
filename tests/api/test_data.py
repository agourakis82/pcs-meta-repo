"""Tests for data endpoints."""

from fastapi.testclient import TestClient


def test_list_ag5_datasets(client: TestClient):
    """Test listing AG5 datasets endpoint."""
    response = client.get("/data/ag5/datasets")
    assert response.status_code == 200

    data = response.json()
    assert "datasets" in data
    assert isinstance(data["datasets"], list)


def test_get_ag5_dataset_not_found(client: TestClient):
    """Test getting non-existent AG5 dataset returns 404."""
    response = client.get("/data/ag5/datasets/nonexistent")
    assert response.status_code == 404


def test_search_ag5_datasets(client: TestClient):
    """Test searching AG5 datasets."""
    response = client.get("/data/ag5/datasets", params={"search": "test"})
    assert response.status_code == 200

    data = response.json()
    assert "datasets" in data
    assert isinstance(data["datasets"], list)


def test_list_helio_summaries(client: TestClient):
    """Test listing HELIO summaries endpoint."""
    response = client.get("/data/helio/summaries")
    assert response.status_code == 200

    data = response.json()
    assert "summaries" in data
    assert isinstance(data["summaries"], list)


def test_get_helio_summary_not_found(client: TestClient):
    """Test getting non-existent HELIO summary returns 404."""
    response = client.get("/data/helio/summaries/nonexistent")
    assert response.status_code == 404


def test_search_helio_summaries(client: TestClient):
    """Test searching HELIO summaries."""
    response = client.get("/data/helio/summaries", params={"search": "test"})
    assert response.status_code == 200

    data = response.json()
    assert "summaries" in data
    assert isinstance(data["summaries"], list)


def test_data_health(client: TestClient):
    """Test data health endpoint."""
    response = client.get("/data/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ["ready", "unavailable", "error"]
