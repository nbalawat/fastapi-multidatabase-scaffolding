"""
Authentication router for the application.

This module provides API routes for authentication-related operations.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.db.base import DatabaseAdapter
from app.api.dependencies.db import get_db_adapter
from app.models.auth.controller import AuthController
from app.models.auth.model import Token, RegisterRequest
from app.models.users.model import UserCreate, User
from app.core.permissions import get_permission_registry
from app.core.security import get_current_active_user, RBACMiddleware

# Define models for roles and permissions response
class Permission(BaseModel):
    id: str
    description: str

class Role(BaseModel):
    id: str
    description: str
    permissions: List[str]

class RolesPermissionsResponse(BaseModel):
    roles: Dict[str, Role]
    permissions: Dict[str, str]

# Create a router for authentication endpoints
router = APIRouter(tags=["authentication"])

@router.post("/token", response_model=Token, summary="Login and get access token", 
             description="OAuth2 compatible token login, get an access token for future requests")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> Token:
    """Authenticate a user and return an access token.
    
    Args:
        form_data: The login form data
        db_adapter: The database adapter
        
    Returns:
        A token for the authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    auth_controller = AuthController(db_adapter)
    token = await auth_controller.login(form_data.username, form_data.password)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_create: UserCreate,
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> User:
    """Register a new user.
    
    Args:
        user_create: The user creation data
        db_adapter: The database adapter
        
    Returns:
        The created user
        
    Raises:
        HTTPException: If the username is already taken
    """
    auth_controller = AuthController(db_adapter)
    created_user = await auth_controller.register(user_create.dict())
    
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Return the created user
    return User(**created_user)

@router.get("/roles-permissions", response_model=RolesPermissionsResponse, summary="Get available roles and permissions")
async def get_roles_and_permissions(
    current_user: User = Depends(RBACMiddleware.has_permission(["roles:read"]))
) -> RolesPermissionsResponse:
    """Get all available roles and permissions in the system.
    
    This endpoint requires the 'roles:read' permission.
    
    Returns:
        A dictionary containing all roles and permissions
    """
    permission_registry = get_permission_registry()
    
    # Get all roles and permissions from the registry
    roles = permission_registry.get_roles()
    permissions = permission_registry.get_permissions()
    
    # Convert to response model format
    roles_dict = {}
    for role_id, role_data in roles.items():
        roles_dict[role_id] = Role(
            id=role_id,
            description=role_data["description"],
            permissions=role_data["permissions"]
        )
    
    return RolesPermissionsResponse(
        roles=roles_dict,
        permissions=permissions
    )
