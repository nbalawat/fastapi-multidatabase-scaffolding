"""API routes for notes using MongoDB."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.security import OAuth2PasswordBearer

from app.api.dependencies import get_current_active_user, get_current_user, get_db_adapter
from app.db.base import DatabaseAdapter
from app.models.notes import NoteCreate, NoteResponse, NoteUpdate, NoteVisibility
from app.models.users import Role, User

# Create router
router = APIRouter(tags=["notes"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note",
    description="Create a new note in MongoDB. Requires authentication.",
)
async def create_note(
    note: NoteCreate,
    current_user: User = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> NoteResponse:
    """Create a new note.
    
    Args:
        note: The note to create
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        The created note
    """
    # Prepare note data
    note_data = note.model_dump()
    note_data["user_id"] = current_user.username  # Use username as the user identifier
    note_data["created_at"] = datetime.utcnow()
    
    # Create note in database
    created_note = await db_adapter.create("notes", note_data)
    
    return NoteResponse(**created_note)


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get a note by ID",
    description="Get a note by its ID. Users can only access their own notes or public notes.",
)
async def get_note(
    note_id: str = Path(..., description="The ID of the note to get"),
    current_user: User = Depends(get_current_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> NoteResponse:
    """Get a note by ID.
    
    Args:
        note_id: The ID of the note to get
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        The note
        
    Raises:
        HTTPException: If the note is not found or the user doesn't have permission
    """
    # Get note from database
    note = await db_adapter.read("notes", note_id)
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    
    # Check if user has permission to access this note
    user_role = current_user.role
    if isinstance(user_role, Role):
        user_role = user_role.value
        
    if (
        note["user_id"] != current_user.username
        and note.get("visibility") != NoteVisibility.PUBLIC.value
        and user_role != Role.ADMIN.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this note",
        )
    
    return NoteResponse(**note)


@router.get(
    "",
    response_model=List[NoteResponse],
    summary="List notes",
    description="List notes with pagination and optional filtering. Users can only see their own notes and public notes.",
)
async def list_notes(
    skip: int = Query(0, ge=0, description="Number of notes to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of notes to return"),
    tag: Optional[str] = Query(None, description="Filter notes by tag"),
    visibility: Optional[NoteVisibility] = Query(None, description="Filter notes by visibility"),
    current_user: User = Depends(get_current_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> List[NoteResponse]:
    """List notes with pagination and optional filtering.
    
    Args:
        skip: Number of notes to skip
        limit: Maximum number of notes to return
        tag: Filter notes by tag
        visibility: Filter notes by visibility
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        A list of notes
    """
    # Prepare query
    query = {}
    
    # Users can only see their own notes and public notes
    if current_user.role != Role.ADMIN.value:
        query["$or"] = [
            {"user_id": current_user.username},
            {"visibility": NoteVisibility.PUBLIC.value},
        ]
    
    # Add tag filter if provided
    if tag:
        query["tags"] = tag
    
    # Add visibility filter if provided
    if visibility:
        query["visibility"] = visibility.value
    
    # Get notes from database
    notes = await db_adapter.list("notes", skip=skip, limit=limit, query=query)
    
    return [NoteResponse(**note) for note in notes]


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update a note",
    description="Update a note by its ID. Users can only update their own notes.",
)
async def update_note(
    note_update: NoteUpdate,
    note_id: str = Path(..., description="The ID of the note to update"),
    current_user: User = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> NoteResponse:
    """Update a note.
    
    Args:
        note_update: The note update data
        note_id: The ID of the note to update
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        The updated note
        
    Raises:
        HTTPException: If the note is not found or the user doesn't have permission
    """
    # Get existing note
    existing_note = await db_adapter.read("notes", note_id)
    
    if not existing_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    
    # Check if user has permission to update this note
    user_role = current_user.role
    if isinstance(user_role, Role):
        user_role = user_role.value
        
    if existing_note["user_id"] != current_user.username and user_role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this note",
        )
    
    # Prepare update data
    update_data = note_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    # Update note in database
    updated_note = await db_adapter.update("notes", note_id, update_data)
    
    if not updated_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    
    return NoteResponse(**updated_note)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note",
    description="Delete a note by its ID. Users can only delete their own notes.",
)
async def delete_note(
    note_id: str = Path(..., description="The ID of the note to delete"),
    current_user: User = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> None:
    """Delete a note.
    
    Args:
        note_id: The ID of the note to delete
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Raises:
        HTTPException: If the note is not found or the user doesn't have permission
    """
    # Get existing note
    existing_note = await db_adapter.read("notes", note_id)
    
    if not existing_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    
    # Check if user has permission to delete this note
    user_role = current_user.role
    if isinstance(user_role, Role):
        user_role = user_role.value
        
    if existing_note["user_id"] != current_user.username and user_role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this note",
        )
    
    # Delete note from database
    deleted = await db_adapter.delete("notes", note_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )


# Admin-only endpoints
@router.get(
    "/admin/notes",
    response_model=List[NoteResponse],
    summary="Admin: List all notes",
    description="List all notes in the system. Admin only.",
)
async def admin_list_all_notes(
    skip: int = Query(0, ge=0, description="Number of notes to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of notes to return"),
    current_user: User = Depends(get_current_active_user),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
) -> List[NoteResponse]:
    """List all notes in the system. Admin only.
    
    Args:
        skip: Number of notes to skip
        limit: Maximum number of notes to return
        current_user: The current authenticated user
        db_adapter: The database adapter
        
    Returns:
        A list of all notes
        
    Raises:
        HTTPException: If the user is not an admin
    """
    # Check if user is admin
    user_role = current_user.role
    if isinstance(user_role, Role):
        user_role = user_role.value
        
    if user_role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    # Get all notes from database
    notes = await db_adapter.list("notes", skip=skip, limit=limit)
    
    return [NoteResponse(**note) for note in notes]
