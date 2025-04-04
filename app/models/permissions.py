"""Permission models for role-based access control."""
from enum import Enum, auto
from typing import List, Optional, Set

from pydantic import BaseModel, Field


class Permission(str, Enum):
    """Permission types for role-based access control."""
    
    # User management permissions
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Note management permissions
    NOTE_CREATE = "note:create"
    NOTE_READ = "note:read"
    NOTE_UPDATE = "note:update"
    NOTE_DELETE = "note:delete"
    
    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    ROLE_MANAGE = "role:manage"


class PermissionSet(BaseModel):
    """A set of permissions."""
    
    permissions: Set[Permission] = Field(default_factory=set)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if the permission set has a specific permission.
        
        Args:
            permission: The permission to check
            
        Returns:
            True if the permission is in the set, False otherwise
        """
        return permission in self.permissions
    
    def add_permission(self, permission: Permission) -> None:
        """Add a permission to the set.
        
        Args:
            permission: The permission to add
        """
        self.permissions.add(permission)
    
    def remove_permission(self, permission: Permission) -> None:
        """Remove a permission from the set.
        
        Args:
            permission: The permission to remove
        """
        self.permissions.discard(permission)


class RolePermissions(BaseModel):
    """Role with associated permissions."""
    
    name: str
    description: Optional[str] = None
    permissions: Set[Permission] = Field(default_factory=set)
    
    class Config:
        """Pydantic model configuration."""
        
        json_schema_extra = {
            "example": {
                "name": "editor",
                "description": "Can create and edit notes",
                "permissions": [
                    "note:create",
                    "note:read",
                    "note:update"
                ]
            }
        }


# Default role permissions
DEFAULT_ROLE_PERMISSIONS = {
    "admin": RolePermissions(
        name="admin",
        description="Administrator with full access",
        permissions={
            Permission.USER_CREATE,
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.USER_DELETE,
            Permission.NOTE_CREATE,
            Permission.NOTE_READ,
            Permission.NOTE_UPDATE,
            Permission.NOTE_DELETE,
            Permission.ADMIN_ACCESS,
            Permission.ROLE_MANAGE,
        }
    ),
    "user": RolePermissions(
        name="user",
        description="Regular user with standard access",
        permissions={
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.NOTE_CREATE,
            Permission.NOTE_READ,
            Permission.NOTE_UPDATE,
            Permission.NOTE_DELETE,
        }
    ),
    "guest": RolePermissions(
        name="guest",
        description="Guest with limited access",
        permissions={
            Permission.USER_READ,
            Permission.NOTE_READ,
        }
    ),
}
