"""API routes for role management."""
from typing import Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.api.dependencies import get_current_active_user, get_db_adapter
from app.db.base import DatabaseAdapter
from app.models.permissions import DEFAULT_ROLE_PERMISSIONS, Permission, RolePermissions
from app.models.users import Role, User

# Create router
router = APIRouter(tags=["roles"])


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
    
    # Get roles from database
    roles = await db_adapter.list("roles")
    
    # If no roles in database, return default roles
    if not roles:
        return list(DEFAULT_ROLE_PERMISSIONS.values())
    
    return [RolePermissions(**role) for role in roles]


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
    
    # Try to get role from database
    role = await db_adapter.read("roles", role_name)
    
    # If role not in database, check default roles
    if not role and role_name in DEFAULT_ROLE_PERMISSIONS:
        return DEFAULT_ROLE_PERMISSIONS[role_name]
    elif not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_name} not found",
        )
    
    return RolePermissions(**role)


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
    
    # Check if role already exists
    existing_role = await db_adapter.read("roles", role.name)
    
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role {role.name} already exists",
        )
    
    # Create role in database
    role_data = role.model_dump()
    role_data["permissions"] = [p for p in role.permissions]  # Convert set to list for storage
    
    created_role = await db_adapter.create("roles", role_data)
    
    # Convert permissions back to set
    created_role["permissions"] = set(created_role["permissions"])
    
    return RolePermissions(**created_role)


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
        HTTPException: If the user is not an admin or the role is not found
    """
    # Check if user is admin
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    # Check if role exists
    existing_role = await db_adapter.read("roles", role_name)
    
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_name} not found",
        )
    
    # Prevent changing built-in roles
    if role_name in DEFAULT_ROLE_PERMISSIONS and role_update.name != role_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot change name of built-in role {role_name}",
        )
    
    # Update role in database
    role_data = role_update.model_dump()
    role_data["permissions"] = [p for p in role_update.permissions]  # Convert set to list for storage
    
    updated_role = await db_adapter.update("roles", role_name, role_data)
    
    if not updated_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_name} not found",
        )
    
    # Convert permissions back to set
    updated_role["permissions"] = set(updated_role["permissions"])
    
    return RolePermissions(**updated_role)


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
    
    # Prevent deleting built-in roles
    if role_name in DEFAULT_ROLE_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete built-in role {role_name}",
        )
    
    # Delete role from database
    deleted = await db_adapter.delete("roles", role_name)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_name} not found",
        )


@router.get(
    "/permissions",
    response_model=List[str],
    summary="List all permissions",
    description="List all available permissions. Admin only.",
)
async def list_permissions(
    current_user: User = Depends(get_current_active_user),
) -> List[str]:
    """List all available permissions.
    
    Args:
        current_user: The current authenticated user
        
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
    
    # Return all permissions
    return [p.value for p in Permission]
