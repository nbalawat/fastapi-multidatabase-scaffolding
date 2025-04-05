from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
import logging

from app.models.notes.model import NoteCreate, NoteUpdate, Note
from app.models.notes.controller import NotesController
from app.api.dependencies.db import get_db_adapter
from app.api.dependencies import get_current_active_user
from app.models.users.model import User
from app.utils.generic.router_utils import create_standard_routes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes", tags=["notes"])

# Create custom routes with authentication
@router.post("/", response_model=Note)
async def create_note(
    note: NoteCreate,
    db_adapter=Depends(get_db_adapter),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new note with the current user's ID."""
    controller = NotesController(db_adapter)
    # Pass the current user to the controller
    result = await controller.create_with_user(note, current_user)
    return result

# Create other standard CRUD routes except create
@router.get("/{item_id}", response_model=Note)
async def read_note(item_id: str, db_adapter=Depends(get_db_adapter)):
    """Get a note by ID."""
    controller = NotesController(db_adapter)
    result = await controller.read(item_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Note with ID {item_id} not found")
    return result

@router.put("/{item_id}", response_model=Note)
async def update_note(
    item_id: str, 
    note: NoteUpdate, 
    db_adapter=Depends(get_db_adapter),
    current_user: User = Depends(get_current_active_user)
):
    """Update a note by ID."""
    controller = NotesController(db_adapter)
    result = await controller.update(item_id, note)
    if not result:
        raise HTTPException(status_code=404, detail=f"Note with ID {item_id} not found")
    return result

@router.delete("/{item_id}", response_model=Note)
async def delete_note(
    item_id: str, 
    db_adapter=Depends(get_db_adapter),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a note by ID."""
    controller = NotesController(db_adapter)
    result = await controller.delete(item_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Note with ID {item_id} not found")
    return result

@router.get("/", response_model=List[Note])
async def list_notes(
    skip: int = 0, 
    limit: int = 100, 
    db_adapter=Depends(get_db_adapter),
    current_user: User = Depends(get_current_active_user)
):
    """List all notes."""
    controller = NotesController(db_adapter)
    result = await controller.list(skip, limit)
    return result

# Add custom routes if needed
@router.get("/by-tag/{tag}", response_model=List[Note])
async def get_notes_by_tag(
    tag: str,
    skip: int = 0,
    limit: int = 100,
    db_adapter=Depends(get_db_adapter)
):
    """Get notes by tag."""
    controller = NotesController(db_adapter)
    result = await controller.list(skip, limit, {"tag": tag})
    return result
