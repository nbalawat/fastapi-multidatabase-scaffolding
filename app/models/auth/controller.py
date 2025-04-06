"""
Authentication controller for the application.

This module provides functionality for user authentication and registration.
"""
from typing import Dict, Any, Optional
import logging

from app.db.base import DatabaseAdapter
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import get_settings
from app.models.users.model import UserInDB, Role, User
from app.models.auth.model import Token
from app.core.permissions import get_permission_registry

logger = logging.getLogger(__name__)

class AuthController:
    """Controller for handling authentication operations."""
    
    def __init__(self, db_adapter: DatabaseAdapter):
        """Initialize the controller with a database adapter.
        
        Args:
            db_adapter: The database adapter to use for operations
        """
        self.db = db_adapter
        
    async def login(self, username: str, password: str) -> Optional[Token]:
        """Authenticate a user and return an access token.
        
        Args:
            username: The username to authenticate
            password: The password to verify
            
        Returns:
            A token for the authenticated user, or None if authentication fails
        """
        # Get the user from the database
        user_data = await self.db.read("users", username, field="username")
        
        # Check if the user exists
        if not user_data:
            logger.warning(f"Login attempt with non-existent username: {username}")
            return None
        
        # Create a UserInDB model from the database data
        user = UserInDB(**user_data)
        
        # Verify the password
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for user: {username}")
            return None
        
        # Get the permission registry
        permission_registry = get_permission_registry()
        
        # Get the user's role
        user_role = user.role.value if isinstance(user.role, Role) else user.role
        
        # Get permissions for the user's role
        role_permissions = permission_registry.get_role_permissions(user_role)
        
        # Create a token for the user with role and permissions
        token_data = {
            "sub": user.username,
            "role": user_role,
            "roles": [user_role],  # Include as a list for the RBAC middleware
            "permissions": role_permissions,  # Include permissions from the role
        }
        
        # Get settings for token creation
        settings = get_settings()
        
        # Create and return the token
        access_token = create_access_token(token_data, settings)
        
        logger.info(f"Successful login for user: {username}")
        return Token(access_token=access_token, token_type="bearer")
    
    async def register(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Register a new user.
        
        Args:
            user_data: The user data to register
            
        Returns:
            The created user data, or None if registration fails
        """
        # Check if the username is already taken
        existing_user = await self.db.read("users", user_data["username"], field="username")
        if existing_user:
            logger.warning(f"Registration attempt with existing username: {user_data['username']}")
            return None
        
        # Hash the password
        hashed_password = get_password_hash(user_data["password"])
        
        # Create the user data for the database
        db_user_data = user_data.copy()
        db_user_data.pop("password")  # Remove the plain password
        db_user_data["hashed_password"] = hashed_password
        
        # Ensure role is always set to a valid value
        if not db_user_data.get("role"):
            db_user_data["role"] = Role.USER.value
            
        # Ensure is_active is always set to a boolean value
        if "is_active" not in db_user_data or db_user_data["is_active"] is None:
            db_user_data["is_active"] = True
        
        # Create the user in the database
        created_user = await self.db.create("users", db_user_data)
        
        logger.info(f"User registered successfully: {db_user_data['username']}")
        return created_user
