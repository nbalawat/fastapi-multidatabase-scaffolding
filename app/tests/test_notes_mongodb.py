"""Tests for the notes API with MongoDB."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models.users import Role, User
from app.models.permissions import Permission


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user."""
    return User(
        id="1",
        username="admin",
        email="admin@example.com",
        full_name="Administrator",
        role=Role.ADMIN.value,
        is_active=True
    )


@pytest.fixture
def mock_regular_user():
    """Create a mock regular user."""
    return User(
        id="2",
        username="user",
        email="user@example.com",
        full_name="Regular User",
        role=Role.USER.value,
        is_active=True
    )


@pytest.fixture
def mock_guest_user():
    """Create a mock guest user."""
    return User(
        id="3",
        username="guest",
        email="guest@example.com",
        full_name="Guest User",
        role=Role.GUEST.value,
        is_active=True
    )


@pytest.fixture
def mock_db_adapter():
    """Create a mock database adapter."""
    with patch("app.api.dependencies.get_db_adapter") as mock_get_db:
        mock_adapter = AsyncMock()
        mock_get_db.return_value = mock_adapter
        yield mock_adapter


@pytest.mark.asyncio
class TestNotesAPI:
    """Tests for the notes API endpoints with MongoDB."""
    
    async def test_create_note_user(self, test_client, mock_regular_user, mock_db_adapter):
        """Test creating a note as a regular user."""
        # Mock the current user dependency to return a regular user
        with patch("app.api.routes.notes.get_current_active_user", return_value=mock_regular_user):
            # Mock the permission check
            with patch("app.api.routes.notes.has_permission", return_value=lambda: mock_regular_user):
                # Mock the database adapter to create a note
                mock_db_adapter.create.return_value = {
                    "id": "note123",
                    "title": "Test Note",
                    "content": "This is a test note",
                    "visibility": "private",
                    "tags": ["test"],
                    "created_by": "2",
                    "created_at": "2025-04-04T09:00:00.000Z",
                    "updated_at": "2025-04-04T09:00:00.000Z"
                }
                
                # Note data to create
                note_data = {
                    "title": "Test Note",
                    "content": "This is a test note",
                    "visibility": "private",
                    "tags": ["test"]
                }
                
                # Make the request
                response = test_client.post("/api/v1/notes", json=note_data)
                
                # Check the response
                assert response.status_code == 201
                note = response.json()
                assert note["id"] == "note123"
                assert note["title"] == "Test Note"
                assert note["created_by"] == "2"
                
                # Verify the database adapter was called correctly
                mock_db_adapter.create.assert_called_once()
    
    async def test_create_note_guest(self, test_client, mock_guest_user, mock_db_adapter):
        """Test that guests cannot create notes."""
        # Mock the current user dependency to return a guest user
        with patch("app.api.routes.notes.get_current_active_user", return_value=mock_guest_user):
            # Mock the permission check to raise a 403 error
            with patch("app.api.routes.notes.has_permission", side_effect=Exception("Permission denied")):
                # Note data to create
                note_data = {
                    "title": "Test Note",
                    "content": "This is a test note",
                    "visibility": "private",
                    "tags": ["test"]
                }
                
                # Make the request
                response = test_client.post("/api/v1/notes", json=note_data)
                
                # Check the response
                assert response.status_code == 403
    
    async def test_get_note_by_id(self, test_client, mock_regular_user, mock_db_adapter):
        """Test getting a note by ID."""
        # Mock the current user dependency to return a regular user
        with patch("app.api.routes.notes.get_current_active_user", return_value=mock_regular_user):
            # Mock the permission check
            with patch("app.api.routes.notes.has_permission", return_value=lambda: mock_regular_user):
                # Mock the database adapter to return a note
                mock_db_adapter.read.return_value = {
                    "id": "note123",
                    "title": "Test Note",
                    "content": "This is a test note",
                    "visibility": "private",
                    "tags": ["test"],
                    "created_by": "2",
                    "created_at": "2025-04-04T09:00:00.000Z",
                    "updated_at": "2025-04-04T09:00:00.000Z"
                }
                
                # Make the request
                response = test_client.get("/api/v1/notes/note123")
                
                # Check the response
                assert response.status_code == 200
                note = response.json()
                assert note["id"] == "note123"
                assert note["title"] == "Test Note"
                assert note["created_by"] == "2"
                
                # Verify the database adapter was called correctly
                mock_db_adapter.read.assert_called_once_with("notes", "note123")
    
    async def test_get_note_not_found(self, test_client, mock_regular_user, mock_db_adapter):
        """Test getting a non-existent note."""
        # Mock the current user dependency to return a regular user
        with patch("app.api.routes.notes.get_current_active_user", return_value=mock_regular_user):
            # Mock the permission check
            with patch("app.api.routes.notes.has_permission", return_value=lambda: mock_regular_user):
                # Mock the database adapter to return None (note not found)
                mock_db_adapter.read.return_value = None
                
                # Make the request
                response = test_client.get("/api/v1/notes/nonexistent")
                
                # Check the response
                assert response.status_code == 404
                assert "not found" in response.json()["detail"]
    
    async def test_update_note(self, test_client, mock_regular_user, mock_db_adapter):
        """Test updating a note."""
        # Mock the current user dependency to return a regular user
        with patch("app.api.routes.notes.get_current_active_user", return_value=mock_regular_user):
            # Mock the permission check
            with patch("app.api.routes.notes.has_permission", return_value=lambda: mock_regular_user):
                # Mock the database adapter to return a note and update it
                mock_db_adapter.read.return_value = {
                    "id": "note123",
                    "title": "Test Note",
                    "content": "This is a test note",
                    "visibility": "private",
                    "tags": ["test"],
                    "created_by": "2",
                    "created_at": "2025-04-04T09:00:00.000Z",
                    "updated_at": "2025-04-04T09:00:00.000Z"
                }
                mock_db_adapter.update.return_value = {
                    "id": "note123",
                    "title": "Updated Note",
                    "content": "This note has been updated",
                    "visibility": "private",
                    "tags": ["test", "updated"],
                    "created_by": "2",
                    "created_at": "2025-04-04T09:00:00.000Z",
                    "updated_at": "2025-04-04T10:00:00.000Z"
                }
                
                # Note data to update
                update_data = {
                    "title": "Updated Note",
                    "content": "This note has been updated",
                    "tags": ["test", "updated"]
                }
                
                # Make the request
                response = test_client.put("/api/v1/notes/note123", json=update_data)
                
                # Check the response
                assert response.status_code == 200
                note = response.json()
                assert note["id"] == "note123"
                assert note["title"] == "Updated Note"
                assert note["content"] == "This note has been updated"
                assert "updated" in note["tags"]
                
                # Verify the database adapter was called correctly
                mock_db_adapter.read.assert_called_once_with("notes", "note123")
                mock_db_adapter.update.assert_called_once()
    
    async def test_delete_note(self, test_client, mock_regular_user, mock_db_adapter):
        """Test deleting a note."""
        # Mock the current user dependency to return a regular user
        with patch("app.api.routes.notes.get_current_active_user", return_value=mock_regular_user):
            # Mock the permission check
            with patch("app.api.routes.notes.has_permission", return_value=lambda: mock_regular_user):
                # Mock the database adapter to return a note and delete it
                mock_db_adapter.read.return_value = {
                    "id": "note123",
                    "title": "Test Note",
                    "content": "This is a test note",
                    "visibility": "private",
                    "tags": ["test"],
                    "created_by": "2",
                    "created_at": "2025-04-04T09:00:00.000Z",
                    "updated_at": "2025-04-04T09:00:00.000Z"
                }
                mock_db_adapter.delete.return_value = True
                
                # Make the request
                response = test_client.delete("/api/v1/notes/note123")
                
                # Check the response
                assert response.status_code == 204
                
                # Verify the database adapter was called correctly
                mock_db_adapter.read.assert_called_once_with("notes", "note123")
                mock_db_adapter.delete.assert_called_once_with("notes", "note123")
    
    async def test_list_notes(self, test_client, mock_regular_user, mock_db_adapter):
        """Test listing notes."""
        # Mock the current user dependency to return a regular user
        with patch("app.api.routes.notes.get_current_active_user", return_value=mock_regular_user):
            # Mock the permission check
            with patch("app.api.routes.notes.has_permission", return_value=lambda: mock_regular_user):
                # Mock the database adapter to return a list of notes
                mock_db_adapter.list.return_value = [
                    {
                        "id": "note123",
                        "title": "Test Note 1",
                        "content": "This is test note 1",
                        "visibility": "private",
                        "tags": ["test"],
                        "created_by": "2",
                        "created_at": "2025-04-04T09:00:00.000Z",
                        "updated_at": "2025-04-04T09:00:00.000Z"
                    },
                    {
                        "id": "note456",
                        "title": "Test Note 2",
                        "content": "This is test note 2",
                        "visibility": "public",
                        "tags": ["test", "public"],
                        "created_by": "2",
                        "created_at": "2025-04-04T10:00:00.000Z",
                        "updated_at": "2025-04-04T10:00:00.000Z"
                    }
                ]
                
                # Make the request
                response = test_client.get("/api/v1/notes")
                
                # Check the response
                assert response.status_code == 200
                notes = response.json()
                assert len(notes) == 2
                assert notes[0]["id"] == "note123"
                assert notes[1]["id"] == "note456"
                
                # Verify the database adapter was called correctly
                mock_db_adapter.list.assert_called_once()
    
    async def test_admin_list_all_notes(self, test_client, mock_admin_user, mock_db_adapter):
        """Test that admins can list all notes."""
        # Mock the current user dependency to return an admin
        with patch("app.api.routes.notes.get_current_active_user", return_value=mock_admin_user):
            # Mock the permission check
            with patch("app.api.routes.notes.has_permission", return_value=lambda: mock_admin_user):
                # Mock the database adapter to return a list of all notes
                mock_db_adapter.list.return_value = [
                    {
                        "id": "note123",
                        "title": "User Note",
                        "content": "This is a user's note",
                        "visibility": "private",
                        "tags": ["test"],
                        "created_by": "2",
                        "created_at": "2025-04-04T09:00:00.000Z",
                        "updated_at": "2025-04-04T09:00:00.000Z"
                    },
                    {
                        "id": "note456",
                        "title": "Admin Note",
                        "content": "This is an admin's note",
                        "visibility": "private",
                        "tags": ["admin"],
                        "created_by": "1",
                        "created_at": "2025-04-04T10:00:00.000Z",
                        "updated_at": "2025-04-04T10:00:00.000Z"
                    },
                    {
                        "id": "note789",
                        "title": "Public Note",
                        "content": "This is a public note",
                        "visibility": "public",
                        "tags": ["public"],
                        "created_by": "3",
                        "created_at": "2025-04-04T11:00:00.000Z",
                        "updated_at": "2025-04-04T11:00:00.000Z"
                    }
                ]
                
                # Make the request
                response = test_client.get("/api/v1/notes/admin/notes")
                
                # Check the response
                assert response.status_code == 200
                notes = response.json()
                assert len(notes) == 3
                
                # Verify the database adapter was called correctly
                mock_db_adapter.list.assert_called_once()
    
    async def test_search_notes(self, test_client, mock_regular_user, mock_db_adapter):
        """Test searching for notes."""
        # Mock the current user dependency to return a regular user
        with patch("app.api.routes.notes.get_current_active_user", return_value=mock_regular_user):
            # Mock the permission check
            with patch("app.api.routes.notes.has_permission", return_value=lambda: mock_regular_user):
                # Mock the database adapter to return search results
                mock_db_adapter.search.return_value = [
                    {
                        "id": "note123",
                        "title": "Important Note",
                        "content": "This is an important test note",
                        "visibility": "private",
                        "tags": ["important", "test"],
                        "created_by": "2",
                        "created_at": "2025-04-04T09:00:00.000Z",
                        "updated_at": "2025-04-04T09:00:00.000Z"
                    }
                ]
                
                # Make the request
                response = test_client.get("/api/v1/notes/search?q=important")
                
                # Check the response
                assert response.status_code == 200
                notes = response.json()
                assert len(notes) == 1
                assert notes[0]["title"] == "Important Note"
                assert "important" in notes[0]["tags"]
                
                # Verify the database adapter was called correctly
                mock_db_adapter.search.assert_called_once()
