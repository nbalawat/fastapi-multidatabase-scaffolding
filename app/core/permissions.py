from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)

# Define all available permissions
PERMISSIONS = {
    # Notes permissions
    "notes:create": "Create new notes",
    "notes:read": "Read notes",
    "notes:update": "Update existing notes",
    "notes:delete": "Delete notes",
    
    # Users permissions
    "users:create": "Create new users",
    "users:read": "Read user information",
    "users:update": "Update user information",
    "users:delete": "Delete users",
    
    # Role management permissions
    "roles:create": "Create new roles",
    "roles:read": "Read role information",
    "roles:update": "Update role information",
    "roles:delete": "Delete roles",
    "roles:assign": "Assign roles to users",
}

# Define roles with their associated permissions
ROLES = {
    "admin": {
        "description": "Administrator with full access",
        "permissions": [
            "notes:create", "notes:read", "notes:update", "notes:delete",
            "users:create", "users:read", "users:update", "users:delete",
            "roles:create", "roles:read", "roles:update", "roles:delete", "roles:assign"
        ]
    },
    "editor": {
        "description": "Can create and edit content",
        "permissions": [
            "notes:create", "notes:read", "notes:update",
            "users:read"
        ]
    },
    "viewer": {
        "description": "Read-only access",
        "permissions": [
            "notes:read",
            "users:read"
        ]
    }
}

class PermissionRegistry:
    """Registry for managing and validating permissions and roles."""
    
    def __init__(self):
        self._permissions: Dict[str, str] = PERMISSIONS.copy()
        self._roles: Dict[str, Dict] = ROLES.copy()
        self._validate_roles()
    
    def _validate_roles(self) -> None:
        """Validate that all permissions in roles exist in the permissions registry."""
        for role_name, role_info in self._roles.items():
            for permission in role_info["permissions"]:
                if permission not in self._permissions:
                    logger.warning(f"Role '{role_name}' contains undefined permission: '{permission}'")
    
    def get_permissions(self) -> Dict[str, str]:
        """Get all registered permissions."""
        return self._permissions.copy()
    
    def get_roles(self) -> Dict[str, Dict]:
        """Get all registered roles."""
        return self._roles.copy()
    
    def validate_permission(self, permission: str) -> bool:
        """Check if a permission is valid."""
        return permission in self._permissions
    
    def validate_permissions(self, permissions: List[str]) -> List[str]:
        """Validate a list of permissions and return only valid ones."""
        return [p for p in permissions if self.validate_permission(p)]
    
    def validate_role(self, role: str) -> bool:
        """Check if a role is valid."""
        return role in self._roles
    
    def get_role_permissions(self, role: str) -> List[str]:
        """Get permissions for a specific role."""
        if not self.validate_role(role):
            return []
        return self._roles[role]["permissions"].copy()
    
    def get_permissions_for_roles(self, roles: List[str]) -> List[str]:
        """Get all permissions for a list of roles."""
        all_permissions: Set[str] = set()
        for role in roles:
            if self.validate_role(role):
                all_permissions.update(self._roles[role]["permissions"])
        return list(all_permissions)
    
    def register_permission(self, permission_id: str, description: str) -> bool:
        """Register a new permission."""
        if permission_id in self._permissions:
            return False
        self._permissions[permission_id] = description
        return True
    
    def register_role(self, role_id: str, description: str, permissions: List[str]) -> bool:
        """Register a new role with permissions."""
        if role_id in self._roles:
            return False
            
        # Validate permissions
        valid_permissions = self.validate_permissions(permissions)
        if len(valid_permissions) != len(permissions):
            logger.warning(f"Some permissions for role '{role_id}' are invalid and will be ignored")
            
        self._roles[role_id] = {
            "description": description,
            "permissions": valid_permissions
        }
        return True

# Create a singleton instance
permission_registry = PermissionRegistry()

def get_permission_registry() -> PermissionRegistry:
    """Get the permission registry instance."""
    return permission_registry
