"""
Authentication router for the application.

This module provides API routes for authentication-related operations.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.db.base import DatabaseAdapter
from app.api.dependencies.db import get_db_adapter
from app.models.auth.controller import AuthController
from app.models.auth.model import Token, RegisterRequest
from app.models.users.model import UserCreate, User

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
