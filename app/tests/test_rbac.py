"""Tests for the Role-Based Access Control (RBAC) system."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.models.permissions import Permission, PermissionSet, RolePermissions
from app.models.users import Role, User
from app.api.dependencies.permissions import has_permission, has_any_permission, has_all_permissions


class TestPermissionModels:
    """Tests for the permission models."""
    
    def test_permission_enum(self):
        """Test the Permission enum."""
        # Check that all expected permissions exist
        assert Permission.USER_CREATE == "user:create"
        assert Permission.NOTE_READ == "note:read"
        assert Permission.ADMIN_ACCESS == "admin:access"
    
    def test_permission_set(self):
        """Test the PermissionSet model."""
        # Create a permission set
        permission_set = PermissionSet()
        
        # Initially empty
        assert len(permission_set.permissions) == 0
        
        # Add permissions
        permission_set.add_permission(Permission.USER_CREATE)
        permission_set.add_permission(Permission.USER_READ)
        
        # Check permissions
        assert permission_set.has_permission(Permission.USER_CREATE)
        assert permission_set.has_permission(Permission.USER_READ)
        assert not permission_set.has_permission(Permission.USER_DELETE)
        
        # Remove a permission
        permission_set.remove_permission(Permission.USER_CREATE)
        
        # Check permissions again
        assert not permission_set.has_permission(Permission.USER_CREATE)
        assert permission_set.has_permission(Permission.USER_READ)
    
    def test_role_permissions(self):
        """Test the RolePermissions model."""
        # Create a role with permissions
        role = RolePermissions(
            name="editor",
            description="Can edit content",
            permissions={Permission.NOTE_CREATE, Permission.NOTE_READ, Permission.NOTE_UPDATE}
        )
        
        # Check role properties
        assert role.name == "editor"
        assert role.description == "Can edit content"
        assert len(role.permissions) == 3
        assert Permission.NOTE_CREATE in role.permissions
        assert Permission.NOTE_READ in role.permissions
        assert Permission.NOTE_UPDATE in role.permissions
        assert Permission.NOTE_DELETE not in role.permissions


@pytest.mark.asyncio
class TestPermissionDependencies:
    """Tests for the permission checking dependencies."""
    
    async def test_has_permission_admin(self):
        """Test that admins always have all permissions."""
        # Create an admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            role=Role.ADMIN.value,
            is_active=True
        )
        
        # Mock the get_current_active_user dependency
        with patch("app.api.dependencies.permissions.get_current_active_user", return_value=admin_user):
            # Mock the database adapter
            with patch("app.api.dependencies.permissions.DatabaseAdapterFactory.get_adapter") as mock_factory:
                mock_adapter = AsyncMock()
                mock_factory.return_value = mock_adapter
                
                # Test the has_permission dependency with any permission
                permission_check = has_permission(Permission.NOTE_DELETE)
                result = await permission_check()
                
                # Admin should have the permission
                assert result == admin_user
    
    async def test_has_permission_user_with_permission(self):
        """Test that users with the required permission pass the check."""
        # Create a regular user
        user = User(
            username="user",
            email="user@example.com",
            role="user",
            is_active=True
        )
        
        # Mock the get_current_active_user dependency
        with patch("app.api.dependencies.permissions.get_current_active_user", return_value=user):
            # Mock the database adapter
            with patch("app.api.dependencies.permissions.DatabaseAdapterFactory.get_adapter") as mock_factory:
                mock_adapter = AsyncMock()
                mock_factory.return_value = mock_adapter
                
                # Mock the get_user_permissions function
                with patch("app.api.dependencies.permissions.get_user_permissions", return_value={Permission.NOTE_READ}):
                    # Test the has_permission dependency with a permission the user has
                    permission_check = has_permission(Permission.NOTE_READ)
                    result = await permission_check()
                    
                    # User should have the permission
                    assert result == user
    
    async def test_has_permission_user_without_permission(self):
        """Test that users without the required permission fail the check."""
        # Create a regular user
        user = User(
            username="user",
            email="user@example.com",
            role="user",
            is_active=True
        )
        
        # Mock the get_current_active_user dependency
        with patch("app.api.dependencies.permissions.get_current_active_user", return_value=user):
            # Mock the database adapter
            with patch("app.api.dependencies.permissions.DatabaseAdapterFactory.get_adapter") as mock_factory:
                mock_adapter = AsyncMock()
                mock_factory.return_value = mock_adapter
                
                # Mock the get_user_permissions function
                with patch("app.api.dependencies.permissions.get_user_permissions", return_value={Permission.NOTE_READ}):
                    # Test the has_permission dependency with a permission the user doesn't have
                    permission_check = has_permission(Permission.NOTE_DELETE)
                    
                    # User should not have the permission
                    with pytest.raises(HTTPException) as excinfo:
                        await permission_check()
                    
                    # Check the exception details
                    assert excinfo.value.status_code == 403
                    assert "Permission note:delete required" in excinfo.value.detail
    
    async def test_has_any_permission(self):
        """Test the has_any_permission dependency."""
        # Create a regular user
        user = User(
            username="user",
            email="user@example.com",
            role="user",
            is_active=True
        )
        
        # Mock the get_current_active_user dependency
        with patch("app.api.dependencies.permissions.get_current_active_user", return_value=user):
            # Mock the database adapter
            with patch("app.api.dependencies.permissions.DatabaseAdapterFactory.get_adapter") as mock_factory:
                mock_adapter = AsyncMock()
                mock_factory.return_value = mock_adapter
                
                # Mock the get_user_permissions function
                with patch("app.api.dependencies.permissions.get_user_permissions", return_value={Permission.NOTE_READ}):
                    # Test the has_any_permission dependency with a list including a permission the user has
                    permission_check = has_any_permission([Permission.NOTE_CREATE, Permission.NOTE_READ])
                    result = await permission_check()
                    
                    # User should have at least one of the permissions
                    assert result == user
                    
                    # Test with a list of permissions the user doesn't have
                    permission_check = has_any_permission([Permission.NOTE_CREATE, Permission.NOTE_DELETE])
                    
                    # User should not have any of the permissions
                    with pytest.raises(HTTPException) as excinfo:
                        await permission_check()
                    
                    # Check the exception details
                    assert excinfo.value.status_code == 403
    
    async def test_has_all_permissions(self):
        """Test the has_all_permissions dependency."""
        # Create a regular user
        user = User(
            username="user",
            email="user@example.com",
            role="user",
            is_active=True
        )
        
        # Mock the get_current_active_user dependency
        with patch("app.api.dependencies.permissions.get_current_active_user", return_value=user):
            # Mock the database adapter
            with patch("app.api.dependencies.permissions.DatabaseAdapterFactory.get_adapter") as mock_factory:
                mock_adapter = AsyncMock()
                mock_factory.return_value = mock_adapter
                
                # Mock the get_user_permissions function
                with patch("app.api.dependencies.permissions.get_user_permissions", return_value={
                    Permission.NOTE_READ, 
                    Permission.NOTE_CREATE
                }):
                    # Test the has_all_permissions dependency with permissions the user has
                    permission_check = has_all_permissions([Permission.NOTE_CREATE, Permission.NOTE_READ])
                    result = await permission_check()
                    
                    # User should have all the permissions
                    assert result == user
                    
                    # Test with a list including permissions the user doesn't have
                    permission_check = has_all_permissions([
                        Permission.NOTE_CREATE, 
                        Permission.NOTE_READ,
                        Permission.NOTE_DELETE
                    ])
                    
                    # User should not have all the permissions
                    with pytest.raises(HTTPException) as excinfo:
                        await permission_check()
                    
                    # Check the exception details
                    assert excinfo.value.status_code == 403
                    assert "Missing required permissions" in excinfo.value.detail
