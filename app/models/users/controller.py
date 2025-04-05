from typing import Dict, List, Optional, Any
import logging
import hashlib
import uuid
from datetime import datetime

from app.db.base import DatabaseAdapter
from app.models.users.model import UserCreate, UserUpdate, User
from app.utils.generic.base_controller import BaseController

logger = logging.getLogger(__name__)

class UsersController(BaseController[UserCreate, UserUpdate, User]):
    """Controller for handling user operations across different database types."""
    
    def __init__(self, db_adapter: DatabaseAdapter):
        """Initialize the controller with a database adapter.
        
        Args:
            db_adapter: The database adapter to use for operations
        """
        super().__init__(db_adapter=db_adapter)
        
        # Set the collection name for this controller
        self.collection = "users"
        
        # Set model types for type checking
        self.create_model = UserCreate
        self.update_model = UserUpdate
        self.response_model = User
    
    def _preprocess_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hash password and prepare user data for creation."""
        # Hash the password
        if "password" in data:
            data["password_hash"] = self._hash_password(data.pop("password"))
        
        return data
    
    def _preprocess_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hash password if provided in update."""
        # Hash the password if provided
        if "password" in data:
            data["password_hash"] = self._hash_password(data.pop("password"))
            
        return data
    
    def _postprocess_read(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive fields from user data."""
        # Remove password hash from response
        if "password_hash" in data:
            data.pop("password_hash")
            
        return data
    
    async def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password.
        
        Args:
            username: The username to authenticate
            password: The password to authenticate
            
        Returns:
            The user if authentication is successful, None otherwise
        """
        logger.info(f"Authenticating user: {username}")
        
        # Find user by username
        users = await self.db.list(self.collection, 0, 1, {"username": username})
        
        if not users:
            logger.warning(f"User {username} not found")
            return None
            
        user = users[0]
        
        # Check password
        if "password_hash" not in user:
            logger.error(f"User {username} has no password hash")
            return None
            
        if not self._verify_password(password, user["password_hash"]):
            logger.warning(f"Invalid password for user {username}")
            return None
            
        # Remove password hash from response
        user.pop("password_hash")
        
        logger.info(f"User {username} authenticated successfully")
        return user
    
    def _hash_password(self, password: str) -> str:
        """Hash a password.
        
        Args:
            password: The password to hash
            
        Returns:
            The hashed password
        """
        # In a real application, use a proper password hashing library like bcrypt
        # This is just a simple example
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against a hash.
        
        Args:
            password: The password to verify
            password_hash: The hash to verify against
            
        Returns:
            True if the password matches the hash, False otherwise
        """
        # In a real application, use a proper password hashing library like bcrypt
        # This is just a simple example
        return self._hash_password(password) == password_hash
