"""
Role router for the application.

This module provides API routes for role management operations.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.db.base import DatabaseAdapter
from app.api.dependencies.db import get_db_adapter
from app.api.dependencies.auth import get_current_active_user
from app.models.roles.controller import RolesController
from app.models.roles.model import RolePermissions
from app.models.users.model import Role, User

# Create router
router = APIRouter(prefix="/roles", tags=["roles"])

@router.get(
    "",
    response_model=List[RolePermissions],
    summary="List all roles",
    description="List all roles and their permissions. Admin only.",
)
async def list_roles(
    current_user: User = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> List[RolePermissions]:
    """List all roles and their permissions.
    
    Args:
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        A list of roles with their permissions
        
    Raises:
        HTTPException: If the user is not an admin
    """
    # Check if user is admin
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    controller = RolesController(db_adapter)
    return await controller.list_roles()

@router.get(
    "/{role_name}",
    response_model=RolePermissions,
    summary="Get role details",
    description="Get details of a specific role. Admin only.",
)
async def get_role(
    role_name: str = Path(..., description="The name of the role to get"),
    current_user: User = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> RolePermissions:
    """Get details of a specific role.
    
    Args:
        role_name: The name of the role to get
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        The role with its permissions
        
    Raises:
        HTTPException: If the user is not an admin or the role is not found
    """
    # Check if user is admin
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    controller = RolesController(db_adapter)
    role = await controller.get_role(role_name)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_name} not found",
        )
    
    return role

@router.post(
    "",
    response_model=RolePermissions,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
    description="Create a new role with permissions. Admin only.",
)
async def create_role(
    role: RolePermissions,
    current_user: User = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> RolePermissions:
    """Create a new role with permissions.
    
    Args:
        role: The role to create
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        The created role
        
    Raises:
        HTTPException: If the user is not an admin or the role already exists
    """
    # Check if user is admin
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    controller = RolesController(db_adapter)
    created_role = await controller.create_role(role.dict())
    
    if not created_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role {role.name} already exists",
        )
    
    return created_role

@router.put(
    "/{role_name}",
    response_model=RolePermissions,
    summary="Update a role",
    description="Update a role's permissions. Admin only.",
)
async def update_role(
    role_update: RolePermissions,
    role_name: str = Path(..., description="The name of the role to update"),
    current_user: User = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> RolePermissions:
    """Update a role's permissions.
    
    Args:
        role_update: The updated role data
        role_name: The name of the role to update
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        The updated role
        
    Raises:
        HTTPException: If the user is not an admin, the role is not found, or it's a built-in role
    """
    # Check if user is admin
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    controller = RolesController(db_adapter)
    updated_role = await controller.update_role(role_name, role_update.dict())
    
    if not updated_role:
        if role_update.name != role_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change name of built-in role {role_name}",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_name} not found",
            )
    
    return updated_role

@router.delete(
    "/{role_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a role",
    description="Delete a role. Cannot delete built-in roles. Admin only.",
)
async def delete_role(
    role_name: str = Path(..., description="The name of the role to delete"),
    current_user: User = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> None:
    """Delete a role.
    
    Args:
        role_name: The name of the role to delete
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Raises:
        HTTPException: If the user is not an admin, the role is not found, or it's a built-in role
    """
    # Check if user is admin
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    controller = RolesController(db_adapter)
    result = await controller.delete_role(role_name)
    
    if not result:
        if role_name in Role.__members__:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete built-in role {role_name}",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_name} not found",
            )

@router.get(
    "/permissions/list",
    response_model=List[str],
    summary="List all permissions",
    description="List all available permissions. Admin only.",
)
async def list_permissions(
    current_user: User = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> List[str]:
    """List all available permissions.
    
    Args:
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        A list of all available permissions
        
    Raises:
        HTTPException: If the user is not an admin
    """
    # Check if user is admin
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    controller = RolesController(db_adapter)
    return await controller.list_permissions()
