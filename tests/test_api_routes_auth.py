from unittest.mock import patch, AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.auth import router as auth_router
from app.core.security import get_password_hash
from app.models.users import UserInDB, Role


@pytest.fixture
def app():
    """Create a test FastAPI application with authentication routes."""
    app = FastAPI()
    app.include_router(auth_router)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_db_adapter():
    """Create a mock database adapter."""
    mock_adapter = AsyncMock()
    
    # Mock user for authentication tests
    test_user = UserInDB(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role=Role.USER,
        hashed_password=get_password_hash("password123")
    )
    
    # Setup mock read method to return the test user
    async def mock_read(collection, id):
        if collection == "users" and id == "testuser":
            return test_user.model_dump()
        return None
    
    mock_adapter.read.side_effect = mock_read
    
    # Setup mock create method
    async def mock_create(collection, data):
        return {**data, "id": "new_user_id"}
    
    mock_adapter.create.side_effect = mock_create
    
    return mock_adapter


def test_login_success(client, mock_db_adapter):
    """Test successful login."""
    # Mock the get_db_adapter function
    with patch("app.api.routes.auth.get_db_adapter", return_value=mock_db_adapter):
        # Make a login request
        response = client.post(
            "/token",
            data={"username": "testuser", "password": "password123"}
        )
        
        # Verify the response
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials(client, mock_db_adapter):
    """Test login with invalid credentials."""
    # Mock the get_db_adapter function
    with patch("app.api.routes.auth.get_db_adapter", return_value=mock_db_adapter):
        # Make a login request with wrong password
        response = client.post(
            "/token",
            data={"username": "testuser", "password": "wrongpassword"}
        )
        
        # Verify the response
        assert response.status_code == 401
        assert "detail" in response.json()
        assert "Incorrect username or password" in response.json()["detail"]


def test_login_user_not_found(client, mock_db_adapter):
    """Test login with non-existent user."""
    # Mock the get_db_adapter function
    with patch("app.api.routes.auth.get_db_adapter", return_value=mock_db_adapter):
        # Make a login request with non-existent user
        response = client.post(
            "/token",
            data={"username": "nonexistent", "password": "password123"}
        )
        
        # Verify the response
        assert response.status_code == 401
        assert "detail" in response.json()
        assert "Incorrect username or password" in response.json()["detail"]


def test_register_user(client, mock_db_adapter):
    """Test user registration."""
    # Mock the get_db_adapter function
    with patch("app.api.routes.auth.get_db_adapter", return_value=mock_db_adapter):
        # Make a registration request
        response = client.post(
            "/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )
        
        # Verify the response
        assert response.status_code == 201
        assert response.json()["username"] == "newuser"
        assert response.json()["email"] == "new@example.com"
        assert "password" not in response.json()
        
        # Verify that create was called with the correct data
        mock_db_adapter.create.assert_called_once()
        call_args = mock_db_adapter.create.call_args[0]
        assert call_args[0] == "users"
        assert "hashed_password" in call_args[1]
        assert call_args[1]["username"] == "newuser"
