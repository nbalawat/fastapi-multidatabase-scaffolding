"""
Role and permission models for the application.

This module defines the data models for role and permission management.
"""
from typing import List, Optional, Set
from pydantic import BaseModel, Field

from app.models.permissions import Permission

class RoleBase(BaseModel):
    """Base model for roles."""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None

class RoleCreate(RoleBase):
    """Model for creating a new role."""
    permissions: List[str] = Field(default_factory=list)

class RoleUpdate(RoleBase):
    """Model for updating an existing role."""
    permissions: List[str] = Field(default_factory=list)

class RolePermissions(RoleBase):
    """Model for a role with its permissions."""
    permissions: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic configuration."""
        from_attributes = True
