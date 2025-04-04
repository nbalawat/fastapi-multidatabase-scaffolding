from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class User(BaseModel):
    """User model for API responses."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: Role = Role.USER
    is_active: bool = True


class UserInDB(User):
    """User model for database storage.
    
    This extends the User model with a hashed password field.
    """
    hashed_password: str
    
    class Config:
        """Pydantic model configuration."""
        # Exclude hashed_password from JSON serialization
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "role": "user",
                "is_active": True
            }
        }
        
        # Exclude sensitive fields from dict representation
        exclude = {"hashed_password"}


class TokenData(BaseModel):
    """Token data model for JWT authentication."""
    username: Optional[str] = None
