"""Tests for MongoDB integration."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.db.mongodb.adapter import MongoDBAdapter
from app.models.users import Role


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_mongodb_adapter():
    """Create a mock MongoDB adapter."""
    with patch("app.api.dependencies.get_db_adapter") as mock_get_db:
        mock_adapter = AsyncMock(spec=MongoDBAdapter)
        mock_get_db.return_value = mock_adapter
        yield mock_adapter


@pytest.mark.asyncio
async def test_create_note(test_client, mock_mongodb_adapter):
    """Test creating a note in MongoDB."""
    # Mock the create method to return a note with an ID
    mock_mongodb_adapter.create.return_value = {
        "id": "60d5ec9af682dbd12a0a9fb9",
        "title": "Test Note",
        "content": "This is a test note",
        "user_id": "1",
        "created_at": "2023-04-04T12:00:00"
    }
    
    # Create a note
    response = test_client.post(
        "/api/v1/notes",
        json={
            "title": "Test Note",
            "content": "This is a test note"
        },
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Check the response
    assert response.status_code == 201
    assert response.json()["title"] == "Test Note"
    assert response.json()["content"] == "This is a test note"
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_get_note(test_client, mock_mongodb_adapter):
    """Test getting a note from MongoDB."""
    # Mock the read method to return a note
    mock_mongodb_adapter.read.return_value = {
        "id": "60d5ec9af682dbd12a0a9fb9",
        "title": "Test Note",
        "content": "This is a test note",
        "user_id": "1",
        "created_at": "2023-04-04T12:00:00"
    }
    
    # Get the note
    response = test_client.get(
        "/api/v1/notes/60d5ec9af682dbd12a0a9fb9",
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["title"] == "Test Note"
    assert response.json()["id"] == "60d5ec9af682dbd12a0a9fb9"


@pytest.mark.asyncio
async def test_list_notes(test_client, mock_mongodb_adapter):
    """Test listing notes from MongoDB."""
    # Mock the list method to return a list of notes
    mock_mongodb_adapter.list.return_value = [
        {
            "id": "60d5ec9af682dbd12a0a9fb9",
            "title": "Test Note 1",
            "content": "This is test note 1",
            "user_id": "1",
            "created_at": "2023-04-04T12:00:00"
        },
        {
            "id": "60d5ec9af682dbd12a0a9fba",
            "title": "Test Note 2",
            "content": "This is test note 2",
            "user_id": "1",
            "created_at": "2023-04-04T12:01:00"
        }
    ]
    
    # List the notes
    response = test_client.get(
        "/api/v1/notes",
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Check the response
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["title"] == "Test Note 1"
    assert response.json()[1]["title"] == "Test Note 2"


@pytest.mark.asyncio
async def test_update_note(test_client, mock_mongodb_adapter):
    """Test updating a note in MongoDB."""
    # Mock the update method to return the updated note
    mock_mongodb_adapter.update.return_value = {
        "id": "60d5ec9af682dbd12a0a9fb9",
        "title": "Updated Note",
        "content": "This note has been updated",
        "user_id": "1",
        "created_at": "2023-04-04T12:00:00",
        "updated_at": "2023-04-04T12:30:00"
    }
    
    # Update the note
    response = test_client.put(
        "/api/v1/notes/60d5ec9af682dbd12a0a9fb9",
        json={
            "title": "Updated Note",
            "content": "This note has been updated"
        },
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Note"
    assert response.json()["content"] == "This note has been updated"


@pytest.mark.asyncio
async def test_delete_note(test_client, mock_mongodb_adapter):
    """Test deleting a note from MongoDB."""
    # Mock the delete method to return True
    mock_mongodb_adapter.delete.return_value = True
    
    # Delete the note
    response = test_client.delete(
        "/api/v1/notes/60d5ec9af682dbd12a0a9fb9",
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Check the response
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_admin_only_endpoint(test_client, mock_mongodb_adapter):
    """Test an admin-only endpoint."""
    # Mock the read method for user verification to return an admin user
    mock_mongodb_adapter.read.return_value = {
        "id": "1",
        "username": "admin",
        "email": "admin@example.com",
        "role": Role.ADMIN.value,
        "is_active": True
    }
    
    # Access the admin-only endpoint
    response = test_client.get(
        "/api/v1/admin/notes",
        headers={"Authorization": "Bearer admin_token"}
    )
    
    # Check the response
    assert response.status_code == 200
