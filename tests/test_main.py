from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch

from app.main import app, get_db_adapter


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


def test_read_root(client):
    """Test the root endpoint returns the expected response."""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()
    assert "version" in response.json()


def test_read_health(client):
    """Test the health endpoint returns a successful response."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_db_adapter():
    """Test that get_db_adapter returns the correct adapter type."""
    with patch("app.main.get_settings") as mock_get_settings:
        # Mock settings to return PostgreSQL as the DB type
        mock_get_settings.return_value.db_type = "postgres"
        
        # Get the adapter
        adapter = get_db_adapter()
        
        # Check that it's the correct type
        from app.db.postgres.adapter import PostgresAdapter
        assert isinstance(adapter, PostgresAdapter)
