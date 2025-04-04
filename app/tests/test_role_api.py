"""Tests for the role management API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models.permissions import Permission, RolePermissions
from app.models.users import Role, User
from app.api.dependencies.auth import get_db_adapter, get_current_active_user
from app.api.routes import roles


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
def mock_db_adapter():
    """Create a mock database adapter."""
    return AsyncMock()


@pytest.mark.asyncio
class TestRoleAPI:
    """Tests for the role management API endpoints."""
    
    async def test_list_roles_admin(self, monkeypatch, test_client, mock_db_adapter, mock_admin_user):
        """Test listing roles as admin."""
        # Configure the mock database adapter to return a list of roles
        mock_db_adapter.list.return_value = [
            {
                "name": "admin",
                "description": "Administrator with full access",
                "permissions": ["user:create", "user:read", "admin:access"]
            },
            {
                "name": "user",
                "description": "Regular user",
                "permissions": ["user:read", "note:read"]
            }
        ]
        
        # Create an async generator that yields the mock adapter
        async def mock_get_db():
            yield mock_db_adapter
            
        # Mock the dependencies
        monkeypatch.setattr(roles, "get_db_adapter", mock_get_db)
        monkeypatch.setattr(roles, "get_current_active_user", lambda: mock_admin_user)
        
        # Make the request
        response = test_client.get("/api/v1/roles")
        
        # Check the response
        assert response.status_code == 200
        roles_data = response.json()
        assert len(roles_data) == 2
        assert roles_data[0]["name"] == "admin"
        assert roles_data[1]["name"] == "user"
        
        # Verify the database adapter was called correctly
        mock_db_adapter.list.assert_called_once_with("roles")
    
    async def test_list_roles_non_admin(self, monkeypatch, test_client, mock_db_adapter, mock_regular_user):
        """Test that non-admins cannot list roles."""
        # Create an async generator that yields the mock adapter
        async def mock_get_db():
            yield mock_db_adapter
            
        # Mock the dependencies
        monkeypatch.setattr(roles, "get_db_adapter", mock_get_db)
        monkeypatch.setattr(roles, "get_current_active_user", lambda: mock_regular_user)
        
        # Make the request
        response = test_client.get("/api/v1/roles")
        
        # Check the response
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    async def test_get_role_admin(self, monkeypatch, test_client, mock_db_adapter, mock_admin_user):
        """Test getting a role as admin."""
        # Configure the mock database adapter to return a role
        mock_db_adapter.read.return_value = {
            "name": "editor",
            "description": "Can edit content",
            "permissions": ["note:create", "note:read", "note:update"]
        }
        
        # Create an async generator that yields the mock adapter
        async def mock_get_db():
            yield mock_db_adapter
            
        # Mock the dependencies
        monkeypatch.setattr(roles, "get_db_adapter", mock_get_db)
        monkeypatch.setattr(roles, "get_current_active_user", lambda: mock_admin_user)
        
        # Make the request
        response = test_client.get("/api/v1/roles/editor")
        
        # Check the response
        assert response.status_code == 200
        role = response.json()
        assert role["name"] == "editor"
        assert role["description"] == "Can edit content"
        assert set(role["permissions"]) == {"note:create", "note:read", "note:update"}
        
        # Verify the database adapter was called correctly
        mock_db_adapter.read.assert_called_once_with("roles", "editor")
    
    async def test_get_role_not_found(self, monkeypatch, test_client, mock_db_adapter, mock_admin_user):
        """Test getting a non-existent role."""
        # Configure the mock database adapter to return None (role not found)
        mock_db_adapter.read.return_value = None
        
        # Create an async generator that yields the mock adapter
        async def mock_get_db():
            yield mock_db_adapter
            
        # Mock the dependencies
        monkeypatch.setattr(roles, "get_db_adapter", mock_get_db)
        monkeypatch.setattr(roles, "get_current_active_user", lambda: mock_admin_user)
        
        # Make the request
        response = test_client.get("/api/v1/roles/nonexistent")
        
        # Check the response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    async def test_create_role_admin(self, monkeypatch, test_client, mock_db_adapter, mock_admin_user):
        """Test creating a role as admin."""
        # Configure the mock database adapter to check if role exists and create it
        mock_db_adapter.read.return_value = None  # Role doesn't exist yet
        mock_db_adapter.create.return_value = {
            "name": "editor",
            "description": "Can edit content",
            "permissions": ["note:create", "note:read", "note:update"]
        }
        
        # Create an async generator that yields the mock adapter
        async def mock_get_db():
            yield mock_db_adapter
            
        # Mock the dependencies
        monkeypatch.setattr(roles, "get_db_adapter", mock_get_db)
        monkeypatch.setattr(roles, "get_current_active_user", lambda: mock_admin_user)
        
        # Role data to create
        role_data = {
            "name": "editor",
            "description": "Can edit content",
            "permissions": ["note:create", "note:read", "note:update"]
        }
        
        # Make the request
        response = test_client.post("/api/v1/roles", json=role_data)
        
        # Check the response
        assert response.status_code == 201
        role = response.json()
        assert role["name"] == "editor"
        assert role["description"] == "Can edit content"
        assert set(role["permissions"]) == {"note:create", "note:read", "note:update"}
        
        # Verify the database adapter was called correctly
        mock_db_adapter.read.assert_called_once_with("roles", "editor")
        mock_db_adapter.create.assert_called_once()
    
    async def test_create_role_already_exists(self, monkeypatch, test_client, mock_db_adapter, mock_admin_user):
        """Test creating a role that already exists."""
        # Configure the mock database adapter to return an existing role
        mock_db_adapter.read.return_value = {
            "name": "reviewer",
            "description": "Can review content",
            "permissions": ["note:read", "note:update"]
        }
        
        # Create an async generator that yields the mock adapter
        async def mock_get_db():
            yield mock_db_adapter
            
        # Mock the dependencies
        monkeypatch.setattr(roles, "get_db_adapter", mock_get_db)
        monkeypatch.setattr(roles, "get_current_active_user", lambda: mock_admin_user)
        
        # Role data to create (same name as existing role)
        role_data = {
            "name": "reviewer",
            "description": "Can review and approve content",
            "permissions": ["note:read", "note:update", "note:approve"]
        }
        
        # Make the request
        response = test_client.post("/api/v1/roles", json=role_data)
        
        # Check the response
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    async def test_update_role_admin(self, monkeypatch, test_client, mock_db_adapter, mock_admin_user):
        """Test updating a role as admin."""
        # Configure the mock database adapter to return an existing role and update it
        mock_db_adapter.read.return_value = {
            "name": "editor",
            "description": "Can edit content",
            "permissions": ["note:create", "note:read", "note:update"]
        }
        mock_db_adapter.update.return_value = {
            "name": "editor",
            "description": "Can edit and delete content",
            "permissions": ["note:create", "note:read", "note:update", "note:delete"]
        }
        
        # Create an async generator that yields the mock adapter
        async def mock_get_db():
            yield mock_db_adapter
            
        # Mock the dependencies
        monkeypatch.setattr(roles, "get_db_adapter", mock_get_db)
        monkeypatch.setattr(roles, "get_current_active_user", lambda: mock_admin_user)
        
        # Role data to update
        role_data = {
            "name": "editor",
            "description": "Can edit and delete content",
            "permissions": ["note:create", "note:read", "note:update", "note:delete"]
        }
        
        # Make the request
        response = test_client.put("/api/v1/roles/editor", json=role_data)
        
        # Check the response
        assert response.status_code == 200
        role = response.json()
        assert role["name"] == "editor"
        assert role["description"] == "Can edit and delete content"
        assert set(role["permissions"]) == {"note:create", "note:read", "note:update", "note:delete"}
        
        # Verify the database adapter was called correctly
        mock_db_adapter.read.assert_called_once_with("roles", "editor")
        mock_db_adapter.update.assert_called_once()
    
    async def test_delete_role_admin(self, monkeypatch, test_client, mock_db_adapter, mock_admin_user):
        """Test deleting a custom role as admin."""
        # Configure the mock database adapter to return an existing role and delete it
        mock_db_adapter.read.return_value = {
            "name": "editor",
            "description": "Can edit content",
            "permissions": ["note:create", "note:read", "note:update"]
        }
        mock_db_adapter.delete.return_value = True
        
        # Create an async generator that yields the mock adapter
        async def mock_get_db():
            yield mock_db_adapter
            
        # Mock the dependencies
        monkeypatch.setattr(roles, "get_db_adapter", mock_get_db)
        monkeypatch.setattr(roles, "get_current_active_user", lambda: mock_admin_user)
        
        # Make the request
        response = test_client.delete("/api/v1/roles/editor")
        
        # Check the response
        assert response.status_code == 200
        assert response.json()["message"] == "Role 'editor' deleted successfully"
        
        # Verify the database adapter was called correctly
        mock_db_adapter.read.assert_called_once_with("roles", "editor")
        mock_db_adapter.delete.assert_called_once_with("roles", "editor")
    
    async def test_delete_builtin_role(self, monkeypatch, test_client, mock_db_adapter, mock_admin_user):
        """Test that built-in roles cannot be deleted."""
        # Create an async generator that yields the mock adapter
        async def mock_get_db():
            yield mock_db_adapter
            
        # Mock the dependencies
        monkeypatch.setattr(roles, "get_db_adapter", mock_get_db)
        monkeypatch.setattr(roles, "get_current_active_user", lambda: mock_admin_user)
        
        # Make the request to delete a built-in role
        response = test_client.delete("/api/v1/roles/admin")
        
        # Check the response
        assert response.status_code == 400
        assert "Cannot delete built-in role" in response.json()["detail"]
        
        # Verify the database adapter was not called
        mock_db_adapter.delete.assert_not_called()
    
    async def test_list_permissions_admin(self, monkeypatch, test_client, mock_db_adapter, mock_admin_user):
        """Test listing all permissions as admin."""
        # Create an async generator that yields the mock adapter
        async def mock_get_db():
            yield mock_db_adapter
            
        # Mock the dependencies
        monkeypatch.setattr(roles, "get_db_adapter", mock_get_db)
        monkeypatch.setattr(roles, "get_current_active_user", lambda: mock_admin_user)
        
        # Make the request
        response = test_client.get("/api/v1/roles/permissions")
        
        # Check the response
        assert response.status_code == 200
        permissions = response.json()
        assert len(permissions) > 0
        assert "user:create" in permissions
        assert "user:read" in permissions
        assert "admin:access" in permissions
