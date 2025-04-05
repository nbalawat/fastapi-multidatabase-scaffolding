"""Permission checking dependencies for API routes."""
from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, status

from app.api.dependencies.auth import get_current_active_user
from app.db.base import DatabaseAdapter, DatabaseAdapterFactory
from app.models.permissions import DEFAULT_ROLE_PERMISSIONS, Permission
from app.models.users.model import Role, User


async def get_user_permissions(user: User, db_adapter: DatabaseAdapter) -> set[Permission]:
    """Get the permissions for a user based on their role.
    
    Args:
        user: The user
        db_adapter: The database adapter
        
    Returns:
        A set of permissions for the user
    """
    # Check if the role is a built-in role
    if user.role in DEFAULT_ROLE_PERMISSIONS:
        return DEFAULT_ROLE_PERMISSIONS[user.role].permissions
    
    # Get the role from the database
    role = await db_adapter.read("roles", user.role)
    
    if not role:
        # If role not found, return an empty set
        return set()
    
    # Convert permissions from list to set
    return set(Permission(p) for p in role.get("permissions", []))


def has_permission(required_permission: Permission) -> Callable:
    """Dependency to check if a user has a specific permission.
    
    Args:
        required_permission: The permission required to access the endpoint
        
    Returns:
        A dependency function that checks if the user has the required permission
    """
    async def check_permission(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """Check if the user has the required permission.
        
        Args:
            current_user: The current authenticated user
            
        Returns:
            The current user if they have the required permission
            
        Raises:
            HTTPException: If the user doesn't have the required permission
        """
        # Admins always have all permissions
        if current_user.role == Role.ADMIN.value:
            return current_user
        
        # Get the database adapter
        db_adapter = DatabaseAdapterFactory.get_adapter()
        await db_adapter.connect()
        
        try:
            # Get the user's permissions
            user_permissions = await get_user_permissions(current_user, db_adapter)
            
            # Check if the user has the required permission
            if required_permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission {required_permission} required",
                )
            
            return current_user
        finally:
            # Disconnect from the database
            await db_adapter.disconnect()
    
    return check_permission


def has_any_permission(required_permissions: List[Permission]) -> Callable:
    """Dependency to check if a user has any of the specified permissions.
    
    Args:
        required_permissions: The permissions required to access the endpoint
        
    Returns:
        A dependency function that checks if the user has any of the required permissions
    """
    async def check_permissions(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """Check if the user has any of the required permissions.
        
        Args:
            current_user: The current authenticated user
            
        Returns:
            The current user if they have any of the required permissions
            
        Raises:
            HTTPException: If the user doesn't have any of the required permissions
        """
        # Admins always have all permissions
        if current_user.role == Role.ADMIN.value:
            return current_user
        
        # Get the database adapter
        db_adapter = DatabaseAdapterFactory.get_adapter()
        await db_adapter.connect()
        
        try:
            # Get the user's permissions
            user_permissions = await get_user_permissions(current_user, db_adapter)
            
            # Check if the user has any of the required permissions
            if not any(perm in user_permissions for perm in required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of the following permissions required: {', '.join(p.value for p in required_permissions)}",
                )
            
            return current_user
        finally:
            # Disconnect from the database
            await db_adapter.disconnect()
    
    return check_permissions


def has_all_permissions(required_permissions: List[Permission]) -> Callable:
    """Dependency to check if a user has all of the specified permissions.
    
    Args:
        required_permissions: The permissions required to access the endpoint
        
    Returns:
        A dependency function that checks if the user has all of the required permissions
    """
    async def check_permissions(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """Check if the user has all of the required permissions.
        
        Args:
            current_user: The current authenticated user
            
        Returns:
            The current user if they have all of the required permissions
            
        Raises:
            HTTPException: If the user doesn't have all of the required permissions
        """
        # Admins always have all permissions
        if current_user.role == Role.ADMIN.value:
            return current_user
        
        # Get the database adapter
        db_adapter = DatabaseAdapterFactory.get_adapter()
        await db_adapter.connect()
        
        try:
            # Get the user's permissions
            user_permissions = await get_user_permissions(current_user, db_adapter)
            
            # Check if the user has all of the required permissions
            missing_permissions = [perm for perm in required_permissions if perm not in user_permissions]
            
            if missing_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(p.value for p in missing_permissions)}",
                )
            
            return current_user
        finally:
            # Disconnect from the database
            await db_adapter.disconnect()
    
    return check_permissions
