"""Authentication dependencies for FastAPI."""
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.security import verify_password
from app.db.base import DatabaseAdapter
from app.models.users.model import User, UserInDB, TokenData
from app.api.dependencies.db import get_db_adapter

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().api_prefix}/token"
)


# get_db_adapter is now imported from app.api.dependencies.db


async def get_user(db, username: str) -> Optional[UserInDB]:
    """Get a user by username.
    
    Args:
        db: Database adapter
        username: Username to look up
        
    Returns:
        UserInDB if found, None otherwise
    """
    # Query by username field instead of using it as an ID
    users = await db.list("users", query={"username": username}, limit=1)
    if users and len(users) > 0:
        return UserInDB(**users[0])
    return None


async def authenticate_user(db, username: str, password: str) -> Optional[User]:
    """Authenticate a user.
    
    Args:
        db: Database adapter
        username: Username to authenticate
        password: Password to verify
        
    Returns:
        User if authentication successful, None otherwise
    """
    user_in_db = await get_user(db, username)
    if not user_in_db:
        return None
    if not verify_password(password, user_in_db.hashed_password):
        return None
    # Return User model (without hashed_password)
    # Convert UUID to string if needed
    user_id = str(user_in_db.id) if hasattr(user_in_db.id, 'hex') else user_in_db.id
    
    return User(
        id=user_id,
        username=user_in_db.username,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        role=user_in_db.role,
        is_active=user_in_db.is_active,
        created_at=user_in_db.created_at,
        updated_at=user_in_db.updated_at,
        hashed_password=user_in_db.hashed_password
    )


async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db_adapter)) -> User:
    """Get the current user from the JWT token.
    
    Args:
        token: JWT token
        db: Database adapter
        
    Returns:
        User if token is valid
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        settings = get_settings()
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    
    user_in_db = await get_user(db, username=token_data.username)
    if user_in_db is None:
        raise credentials_exception
    
    # Return User model (without hashed_password)
    # Convert UUID to string if needed
    user_id = str(user_in_db.id) if hasattr(user_in_db.id, 'hex') else user_in_db.id
    
    return User(
        id=user_id,
        username=user_in_db.username,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        role=user_in_db.role,
        is_active=user_in_db.is_active,
        created_at=user_in_db.created_at,
        updated_at=user_in_db.updated_at,
        hashed_password=user_in_db.hashed_password
    )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user.
    
    Args:
        current_user: Current user
        
    Returns:
        User if active
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
