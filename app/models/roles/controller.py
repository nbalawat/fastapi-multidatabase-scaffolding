"""
Role controller for the application.

This module provides functionality for role management operations.
"""
from typing import Dict, List, Optional, Any
import logging

from app.db.base import DatabaseAdapter
from app.models.roles.model import RolePermissions
from app.models.permissions import DEFAULT_ROLE_PERMISSIONS, Permission
from app.models.users.model import Role

logger = logging.getLogger(__name__)

class RolesController:
    """Controller for handling role operations."""
    
    def __init__(self, db_adapter: DatabaseAdapter):
        """Initialize the controller with a database adapter.
        
        Args:
            db_adapter: The database adapter to use for operations
        """
        self.db = db_adapter
        
    async def list_roles(self) -> List[RolePermissions]:
        """List all roles and their permissions.
        
        Returns:
            A list of roles with their permissions
        """
        # Always return default roles for now to ensure consistent behavior
        logger.info("Using default roles to ensure consistent behavior")
        return list(DEFAULT_ROLE_PERMISSIONS.values())
    
    async def get_role(self, role_name: str) -> Optional[RolePermissions]:
        """Get details of a specific role.
        
        Args:
            role_name: The name of the role to get
            
        Returns:
            The role with its permissions, or None if not found
        """
        logger.info(f"Looking up role: {role_name}")
        
        # Check if role exists in default roles
        if role_name in DEFAULT_ROLE_PERMISSIONS:
            logger.info(f"Found role {role_name} in default roles")
            return DEFAULT_ROLE_PERMISSIONS[role_name]
        else:
            logger.warning(f"Role {role_name} not found in default roles")
            return None
    
    async def create_role(self, role_data: Dict[str, Any]) -> Optional[RolePermissions]:
        """Create a new role with permissions.
        
        Args:
            role_data: The role data to create
            
        Returns:
            The created role, or None if the role already exists
        """
        role_name = role_data["name"]
        
        # Check if role already exists
        if role_name in DEFAULT_ROLE_PERMISSIONS:
            logger.warning(f"Role {role_name} already exists")
            return None
        
        # Create role object
        new_role = RolePermissions(**role_data)
        
        # Add to default roles dictionary
        DEFAULT_ROLE_PERMISSIONS[role_name] = new_role
        
        logger.info(f"Created role {role_name}")
        return new_role
    
    async def update_role(self, role_name: str, role_data: Dict[str, Any]) -> Optional[RolePermissions]:
        """Update a role's permissions.
        
        Args:
            role_name: The name of the role to update
            role_data: The updated role data
            
        Returns:
            The updated role, or None if the role is not found
        """
        # Check if role exists in default roles
        if role_name not in DEFAULT_ROLE_PERMISSIONS:
            logger.warning(f"Role {role_name} not found in default roles")
            return None
        
        logger.info(f"Found role {role_name} in default roles")
        
        # Prevent changing built-in roles
        if role_name in DEFAULT_ROLE_PERMISSIONS and role_data["name"] != role_name:
            logger.warning(f"Cannot change name of built-in role {role_name}")
            return None
        
        # Update role in memory
        logger.info(f"Updating role {role_name} in default roles")
        
        # Create updated role object
        updated_role = {
            "name": role_data["name"],
            "description": role_data["description"],
            "permissions": role_data["permissions"]
        }
        
        # Update in default roles dictionary
        DEFAULT_ROLE_PERMISSIONS[role_name] = RolePermissions(**updated_role)
        
        logger.info(f"Updated role {role_name} in default roles")
        
        return DEFAULT_ROLE_PERMISSIONS[role_name]
    
    async def delete_role(self, role_name: str) -> bool:
        """Delete a role.
        
        Args:
            role_name: The name of the role to delete
            
        Returns:
            True if the role was deleted, False otherwise
        """
        # Prevent deleting built-in roles
        if role_name in Role.__members__:
            logger.warning(f"Cannot delete built-in role {role_name}")
            return False
        
        # Delete role from in-memory dictionary
        logger.info(f"Attempting to delete role {role_name}")
        
        # Check if role exists in our custom roles (not in default roles)
        if role_name not in DEFAULT_ROLE_PERMISSIONS:
            logger.warning(f"Role {role_name} not found in roles dictionary")
            return False
        
        # Remove from dictionary
        del DEFAULT_ROLE_PERMISSIONS[role_name]
        logger.info(f"Deleted role {role_name} from roles dictionary")
        return True
    
    async def list_permissions(self) -> List[str]:
        """List all available permissions.
        
        Returns:
            A list of all available permissions
        """
        logger.info("Listing all permissions")
        # Return all permissions
        permissions = [p.value for p in Permission]
        logger.info(f"Returning {len(permissions)} permissions")
        return permissions
