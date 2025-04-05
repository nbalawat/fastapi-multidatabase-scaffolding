"""Models for notes."""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from uuid import UUID
import uuid

class NoteVisibility(str, Enum):
    """Visibility options for notes."""
    
    PRIVATE = "private"
    PUBLIC = "public"
    SHARED = "shared"


class NoteBase(BaseModel):
    """Base model for notes with common fields."""
    title: str
    content: str
    visibility: NoteVisibility = NoteVisibility.PRIVATE
    tags: List[str] = Field(default_factory=list)
    
class NoteCreate(NoteBase):
    """Model for creating a new note."""
    user_id: Optional[str] = None
    
class NoteUpdate(BaseModel):
    """Model for updating an existing note."""
    title: Optional[str] = None
    content: Optional[str] = None
    visibility: Optional[NoteVisibility] = None
    tags: Optional[List[str]] = None
    
class NoteInDB(NoteBase):
    """Model for note as stored in the database."""
    id: str
    user_id: Union[str, UUID]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True
    }
        
class Note(NoteInDB):
    """Model for note as returned by the API."""
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
