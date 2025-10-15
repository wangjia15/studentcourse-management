"""
Tests for main application endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "grade-management-backend"


def test_openapi_docs():
    """Test OpenAPI documentation endpoint."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data


def test_swagger_ui():
    """Test Swagger UI endpoint."""
    response = client.get("/api/v1/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_redoc():
    """Test ReDoc endpoint."""
    response = client.get("/api/v1/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
