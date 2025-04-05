from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
# Use the full path including API prefix
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password
        
    Returns:
        True if the password matches the hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash.
    
    Args:
        password: The plain text password
        
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    settings: Settings,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.
    
    Args:
        data: The data to encode in the token
        settings: Application settings
        expires_delta: Optional custom expiration time
        
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    
    # Set the expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Get the current user from a JWT token.
    
    Args:
        token: The JWT token
        settings: Application settings
        
    Returns:
        The user data extracted from the token
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Extract the username from the token
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Extract other user data
        role: str = payload.get("role", "user")
        
        # Check if the token has expired
        if "exp" in payload:
            expiration = datetime.fromtimestamp(payload["exp"])
            if datetime.utcnow() > expiration:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
    except JWTError:
        raise credentials_exception
    
    # Return the user data
    return {"username": username, "role": role}


def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get the current active user.
    
    This function can be extended to check if the user is active,
    has been disabled, etc.
    
    Args:
        current_user: The current user data
        
    Returns:
        The current user data if active
        
    Raises:
        HTTPException: If the user is inactive
    """
    # Example: Check if the user is active (can be extended based on your user model)
    # if not current_user.get("is_active", True):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Inactive user"
    #     )
    
    return current_user


def has_role(required_role: str):
    """Create a dependency to check if the current user has a specific role.
    
    Args:
        required_role: The role required to access the endpoint
        
    Returns:
        A dependency function that checks the user's role
    """
    
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
        """Check if the current user has the required role.
        
        Args:
            current_user: The current user data
            
        Returns:
            The current user data if they have the required role
            
        Raises:
            HTTPException: If the user doesn't have the required role
        """
        user_role = current_user.get("role", "user")
        
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        
        return current_user
    
    return role_checker
