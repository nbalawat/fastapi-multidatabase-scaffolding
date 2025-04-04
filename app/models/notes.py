"""Models for notes."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class NoteVisibility(str, Enum):
    """Visibility options for notes."""
    
    PRIVATE = "private"
    PUBLIC = "public"
    SHARED = "shared"


class NoteBase(BaseModel):
    """Base model for notes."""
    
    title: str
    content: str
    visibility: NoteVisibility = NoteVisibility.PRIVATE
    tags: list[str] = Field(default_factory=list)


class NoteCreate(NoteBase):
    """Model for creating a note."""
    pass


class NoteUpdate(BaseModel):
    """Model for updating a note."""
    
    title: Optional[str] = None
    content: Optional[str] = None
    visibility: Optional[NoteVisibility] = None
    tags: Optional[list[str]] = None


class NoteInDB(NoteBase):
    """Model for a note in the database."""
    
    id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class NoteResponse(NoteInDB):
    """Model for a note response."""
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "5f8d0d55b54764421b7056f0",
                "title": "Sample Note",
                "content": "This is a sample note",
                "visibility": "private",
                "tags": ["sample", "note"],
                "user_id": "5f8d0d55b54764421b7056f1",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-02T00:00:00"
            }
        }
    }
