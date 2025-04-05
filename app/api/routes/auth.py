from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import get_settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.db.base import DatabaseAdapter
from app.api.dependencies import get_db_adapter
from app.models.users.model import UserInDB, Role
from app.schemas.users import UserCreate, UserResponse, Token

# Create a router for authentication endpoints
router = APIRouter(tags=["authentication"])


@router.post("/token", response_model=Token, summary="Login and get access token", description="OAuth2 compatible token login, get an access token for future requests")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """Authenticate a user and return an access token.
    
    Args:
        form_data: The login form data
        db_adapter: The database adapter
        
    Returns:
        A token for the authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get the user from the database
    user_data = await db_adapter.read("users", form_data.username)
    
    # Check if the user exists and the password is correct
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create a UserInDB model from the database data
    user = UserInDB(**user_data)
    
    # Verify the password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create a token for the user
    token_data = {
        "sub": user.username,
        "role": user.role.value if isinstance(user.role, Role) else user.role,
    }
    
    # Get settings for token creation
    settings = get_settings()
    
    # Create and return the token
    access_token = create_access_token(token_data, settings)
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_create: UserCreate,
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """Register a new user.
    
    Args:
        user_create: The user creation data
        db_adapter: The database adapter
        
    Returns:
        The created user
        
    Raises:
        HTTPException: If the username is already taken
    """
    # Check if the username is already taken
    existing_user = await db_adapter.read("users", user_create.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Hash the password
    hashed_password = get_password_hash(user_create.password)
    
    # Create the user data for the database
    user_data = user_create.model_dump()
    user_data.pop("password")  # Remove the plain password
    user_data["hashed_password"] = hashed_password
    
    # Ensure role is always set to a valid value
    if not user_data.get("role"):
        user_data["role"] = Role.USER.value
        
    # Ensure is_active is always set to a boolean value
    if "is_active" not in user_data or user_data["is_active"] is None:
        user_data["is_active"] = True
    
    # Create the user in the database
    created_user = await db_adapter.create("users", user_data)
    
    # Return the created user
    return UserResponse(**created_user)
