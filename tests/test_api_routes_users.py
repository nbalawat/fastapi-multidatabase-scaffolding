from unittest.mock import patch, AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.users import router as users_router
from app.core.security import create_access_token
from app.models.users import Role


@pytest.fixture
def app():
    """Create a test FastAPI application with user routes."""
    app = FastAPI()
    app.include_router(users_router)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_db_adapter():
    """Create a mock database adapter."""
    mock_adapter = AsyncMock()
    
    # Mock user data
    users = [
        {
            "id": "1",
            "username": "user1",
            "email": "user1@example.com",
            "full_name": "User One",
            "role": "user",
            "is_active": True,
        },
        {
            "id": "2",
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Admin User",
            "role": "admin",
            "is_active": True,
        },
    ]
    
    # Setup mock list method
    async def mock_list(collection, skip, limit):
        if collection == "users":
            return users[skip:skip + limit]
        return []
    
    mock_adapter.list.side_effect = mock_list
    
    # Setup mock read method
    async def mock_read(collection, id):
        if collection == "users":
            for user in users:
                if user["id"] == id or user["username"] == id:
                    return user
        return None
    
    mock_adapter.read.side_effect = mock_read
    
    # Setup mock update method
    async def mock_update(collection, id, data):
        if collection == "users":
            for user in users:
                if user["id"] == id:
                    updated_user = {**user, **data}
                    return updated_user
        return None
    
    mock_adapter.update.side_effect = mock_update
    
    # Setup mock delete method
    async def mock_delete(collection, id):
        if collection == "users":
            for i, user in enumerate(users):
                if user["id"] == id:
                    return True
        return False
    
    mock_adapter.delete.side_effect = mock_delete
    
    return mock_adapter


@pytest.fixture
def admin_token():
    """Create an admin token for testing."""
    token_data = {"sub": "admin", "role": "admin"}
    return create_access_token(token_data, settings=None)


@pytest.fixture
def user_token():
    """Create a user token for testing."""
    token_data = {"sub": "user1", "role": "user"}
    return create_access_token(token_data, settings=None)


def test_get_users(client, mock_db_adapter, admin_token):
    """Test getting all users."""
    # Mock the get_db_adapter function
    with patch("app.api.routes.users.get_db_adapter", return_value=mock_db_adapter):
        # Make a request with admin token
        response = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Verify the response
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["username"] == "user1"
        assert response.json()[1]["username"] == "admin"


def test_get_users_unauthorized(client, mock_db_adapter, user_token):
    """Test getting all users without admin privileges."""
    # Mock the get_db_adapter function
    with patch("app.api.routes.users.get_db_adapter", return_value=mock_db_adapter):
        # Make a request with user token
        response = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        # Verify the response (should be forbidden)
        assert response.status_code == 403


def test_get_user(client, mock_db_adapter, admin_token):
    """Test getting a specific user."""
    # Mock the get_db_adapter function
    with patch("app.api.routes.users.get_db_adapter", return_value=mock_db_adapter):
        # Make a request with admin token
        response = client.get(
            "/users/1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["username"] == "user1"
        assert response.json()["id"] == "1"


def test_get_user_not_found(client, mock_db_adapter, admin_token):
    """Test getting a non-existent user."""
    # Mock the get_db_adapter function
    with patch("app.api.routes.users.get_db_adapter", return_value=mock_db_adapter):
        # Make a request with admin token
        response = client.get(
            "/users/999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Verify the response
        assert response.status_code == 404
        assert "detail" in response.json()


def test_update_user(client, mock_db_adapter, admin_token):
    """Test updating a user."""
    # Mock the get_db_adapter function
    with patch("app.api.routes.users.get_db_adapter", return_value=mock_db_adapter):
        # Make a request with admin token
        response = client.patch(
            "/users/1",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"full_name": "Updated Name"}
        )
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"
        assert response.json()["username"] == "user1"  # Original data preserved


def test_delete_user(client, mock_db_adapter, admin_token):
    """Test deleting a user."""
    # Mock the get_db_adapter function
    with patch("app.api.routes.users.get_db_adapter", return_value=mock_db_adapter):
        # Make a request with admin token
        response = client.delete(
            "/users/1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Verify the response
        assert response.status_code == 204
