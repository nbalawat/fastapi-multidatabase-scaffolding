from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, List, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging
from functools import wraps

from app.core.config import Settings, get_settings
from app.core.permissions import get_permission_registry

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
# Use the full path including API prefix
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

logger = logging.getLogger(__name__)


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


def decode_token(token: str, settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """Decode a JWT token.
    
    Args:
        token: The JWT token
        settings: Application settings
        
    Returns:
        The decoded token payload or None if invalid
    """
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


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
    
    # Extract permissions and roles if present
    permissions = payload.get("permissions", [])
    roles = payload.get("roles", [role])
    
    # Return the complete user data
    return {
        "username": username, 
        "role": role,
        "roles": roles,
        "permissions": permissions
    }


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


class RBACMiddleware:
    """Middleware for Role-Based Access Control."""
    
    @staticmethod
    def has_permission(required_permissions: List[str]):
        """Dependency for checking if a user has the required permissions.
        
        Args:
            required_permissions: List of permissions required for the endpoint
            
        Returns:
            Dependency function
        """
        # Validate permissions against registry
        permission_registry = get_permission_registry()
        invalid_permissions = [p for p in required_permissions if not permission_registry.validate_permission(p)]
        
        if invalid_permissions:
            logger.warning(f"Invalid permissions specified in route protection: {invalid_permissions}")
            # We don't raise an exception here to avoid breaking the application,
            # but we log a warning to alert developers
        
        async def check_permissions(token: str = Depends(oauth2_scheme)):
            # Get settings and decode token
            settings = get_settings()
            
            # We'll use get_current_user which handles token validation
            try:
                # Pass both token and settings to get_current_user
                user = await get_current_user(token, settings)
            except HTTPException as e:
                # Re-raise the exception with our custom message
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Get user permissions directly and from roles
            user_permissions = user.get("permissions", [])
            user_roles = user.get("roles", [])
            
            # Add permissions from roles
            role_permissions = permission_registry.get_permissions_for_roles(user_roles)
            all_user_permissions = set(user_permissions).union(set(role_permissions))
            
            # Check if user has required permissions
            if not all(perm in all_user_permissions for perm in required_permissions):
                logger.warning(
                    f"User {user.get('username')} does not have required permissions: {required_permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                )
                
            return user
            
        return check_permissions
    
    @staticmethod
    def has_role(required_roles: List[str]):
        """Dependency for checking if a user has the required roles.
        
        Args:
            required_roles: List of roles required for the endpoint
            
        Returns:
            Dependency function
        """
        # Validate roles against registry
        permission_registry = get_permission_registry()
        invalid_roles = [r for r in required_roles if not permission_registry.validate_role(r)]
        
        if invalid_roles:
            logger.warning(f"Invalid roles specified in route protection: {invalid_roles}")
            # We don't raise an exception here to avoid breaking the application,
            # but we log a warning to alert developers
            
        async def check_roles(token: str = Depends(oauth2_scheme)):
            # Get settings and decode token
            settings = get_settings()
            
            # We'll use get_current_user which handles token validation
            try:
                # Pass both token and settings to get_current_user
                user = await get_current_user(token, settings)
            except HTTPException as e:
                # Re-raise the exception with our custom message
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Check if user has required roles
            user_roles = user.get("roles", [])
            if not any(role in user_roles for role in required_roles):
                logger.warning(
                    f"User {user.get('username')} does not have any of the required roles: {required_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                )
                
            return user
            
        return check_roles


def create_rbac_routes(
    router_utils,
    router,
    controller_class,
    create_model,
    update_model,
    response_model,
    get_db_adapter,
    permissions: Dict[str, List[str]]
):
    """Create standard CRUD routes with RBAC.
    
    Args:
        router_utils: The router utilities module
        router: The FastAPI router to add routes to
        controller_class: The controller class to use
        create_model: The model class for create operations
        update_model: The model class for update operations
        response_model: The model class for responses
        get_db_adapter: Function to get the database adapter
        permissions: Dictionary mapping endpoint names to required permissions
    """
    model_name = response_model.__name__.lower()
    
    # Default permissions if not specified
    default_permissions = {
        "create": [f"{model_name}:create"],
        "read": [f"{model_name}:read"],
        "update": [f"{model_name}:update"],
        "delete": [f"{model_name}:delete"],
        "list": [f"{model_name}:read"]
    }
    
    # Merge default permissions with provided permissions
    for key, value in default_permissions.items():
        if key not in permissions:
            permissions[key] = value
    
    @router.post("/", response_model=response_model)
    async def create_item(
        item: create_model, 
        db_adapter=Depends(get_db_adapter),
        user=Depends(RBACMiddleware.has_permission(permissions["create"]))
    ):
        """Create a new item."""
        controller = controller_class(db_adapter)
        result = await controller.create(item)
        return result

    @router.get("/{item_id}", response_model=response_model)
    async def read_item(
        item_id: str, 
        db_adapter=Depends(get_db_adapter),
        user=Depends(RBACMiddleware.has_permission(permissions["read"]))
    ):
        """Get an item by ID."""
        controller = controller_class(db_adapter)
        result = await controller.read(item_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"{model_name} with ID {item_id} not found")
            
        return result

    @router.put("/{item_id}", response_model=response_model)
    async def update_item(
        item_id: str, 
        item: update_model, 
        db_adapter=Depends(get_db_adapter),
        user=Depends(RBACMiddleware.has_permission(permissions["update"]))
    ):
        """Update an item by ID."""
        controller = controller_class(db_adapter)
        result = await controller.update(item_id, item)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"{model_name} with ID {item_id} not found")
            
        return result

    @router.delete("/{item_id}", response_model=bool)
    async def delete_item(
        item_id: str, 
        db_adapter=Depends(get_db_adapter),
        user=Depends(RBACMiddleware.has_permission(permissions["delete"]))
    ):
        """Delete an item by ID."""
        controller = controller_class(db_adapter)
        result = await controller.delete(item_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"{model_name} with ID {item_id} not found")
            
        return result

    @router.get("/", response_model=List[response_model])
    async def list_items(
        skip: int = 0, 
        limit: int = 100, 
        db_adapter=Depends(get_db_adapter),
        user=Depends(RBACMiddleware.has_permission(permissions["list"]))
    ):
        """List items with optional filtering."""
        controller = controller_class(db_adapter)
        result = await controller.list(skip, limit)
        return result
