from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base schema for user data."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @field_validator("password")
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        # Add more password strength validation as needed
        return v


class UserUpdate(UserBase):
    """Schema for updating an existing user."""
    password: Optional[str] = Field(None, min_length=8)
    
    @field_validator("password")
    def password_strength(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength."""
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        # Add more password strength validation as needed
        return v


class UserResponse(UserBase):
    """Schema for user responses from the API."""
    id: str
    username: str
    email: EmailStr
    role: str
    is_active: bool = True


class Token(BaseModel):
    """Schema for authentication tokens."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for data stored in a token."""
    username: str
    role: Optional[str] = None
