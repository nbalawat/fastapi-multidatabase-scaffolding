from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_active_user, has_role
from app.db.base import DatabaseAdapter
from app.api.dependencies import get_db_adapter
from app.schemas.users import UserResponse, UserUpdate

# Create a router for user endpoints
router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_active_user)],
)


@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(has_role("admin")),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """Get all users.
    
    This endpoint is only accessible to administrators.
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        current_user: The current authenticated user (must be an admin)
        db_adapter: The database adapter
        
    Returns:
        A list of users
    """
    users = await db_adapter.list("users", skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """Get a specific user.
    
    Users can view their own profile, but only administrators can view other users.
    
    Args:
        user_id: The ID or username of the user to get
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        The requested user
        
    Raises:
        HTTPException: If the user is not found or the current user doesn't have permission
    """
    # Check if the user is trying to access their own profile or is an admin
    if current_user["username"] != user_id and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get the user from the database
    user = await db_adapter.read("users", user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """Update a user.
    
    Users can update their own profile, but only administrators can update other users.
    
    Args:
        user_id: The ID of the user to update
        user_update: The user update data
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        The updated user
        
    Raises:
        HTTPException: If the user is not found or the current user doesn't have permission
    """
    # Check if the user is trying to update their own profile or is an admin
    if current_user["username"] != user_id and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if the user exists
    existing_user = await db_adapter.read("users", user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    
    # Prepare the update data
    update_data = user_update.model_dump(exclude_unset=True)
    
    # If the password is being updated, hash it
    if "password" in update_data:
        from app.core.security import get_password_hash
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Update the user in the database
    updated_user = await db_adapter.update("users", user_id, update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(has_role("admin")),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """Delete a user.
    
    This endpoint is only accessible to administrators.
    
    Args:
        user_id: The ID of the user to delete
        current_user: The current authenticated user (must be an admin)
        db_adapter: The database adapter
        
    Raises:
        HTTPException: If the user is not found
    """
    # Delete the user from the database
    deleted = await db_adapter.delete("users", user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    
    return None
