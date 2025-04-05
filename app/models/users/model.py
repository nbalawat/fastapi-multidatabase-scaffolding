from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum
from uuid import UUID

class Role(str, Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    EDITOR = "editor"
    USER = "user"
    GUEST = "guest"


class UserBase(BaseModel):
    """Base model for User with common fields."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: Role = Role.USER
    is_active: bool = True
    
class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str
    
class UserUpdate(BaseModel):
    """Model for updating an existing user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    
class UserInDB(UserBase):
    """Model for user as stored in the database.
    
    This extends the User model with a hashed password field.
    """
    id: Union[str, UUID]
    created_at: datetime
    updated_at: Optional[datetime] = None
    hashed_password: str
    
    class Config:
        from_attributes = True
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
        
class User(UserInDB):
    """Model for user as returned by the API."""
    pass


class TokenData(BaseModel):
    """Token data model for JWT authentication."""
    username: Optional[str] = None
