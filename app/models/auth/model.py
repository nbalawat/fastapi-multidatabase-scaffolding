"""
Authentication models for the application.

This module defines the data models for authentication-related operations.
"""
from typing import Optional, Union
from pydantic import BaseModel, Field

class Token(BaseModel):
    """Token model for authentication responses."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data model for JWT payload."""
    username: str
    role: Optional[str] = None
    exp: Optional[int] = None

class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str

class RegisterRequest(BaseModel):
    """Register request model."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: str
    full_name: Optional[str] = None
