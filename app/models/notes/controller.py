from typing import Dict, List, Optional, Any
import logging

from app.db.base import DatabaseAdapter
from app.models.notes.model import NoteCreate, NoteUpdate, Note
from app.models.users.model import User
from app.utils.generic.base_controller import BaseController

logger = logging.getLogger(__name__)

class NotesController(BaseController[NoteCreate, NoteUpdate, Note]):
    """Controller for handling note operations across different database types."""
    
    def __init__(self, db_adapter: DatabaseAdapter):
        """Initialize the controller with a database adapter.
        
        Args:
            db_adapter: The database adapter to use for operations
        """
        super().__init__(db_adapter=db_adapter)
        
        # Set the collection name for this controller
        self.collection = "notes"
        
        # Set model types for type checking
        self.create_model = NoteCreate
        self.update_model = NoteUpdate
        self.response_model = Note
    
    def _preprocess_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure tags is a list when creating a note and add default user_id if not provided.
        
        Args:
            data: The data to preprocess
            
        Returns:
            Preprocessed data
        """
        # If data is a Pydantic model, convert it to a dict first
        if hasattr(data, "model_dump"):
            # Pydantic v2
            data_dict = data.model_dump()
        elif hasattr(data, "dict"):
            # Pydantic v1
            data_dict = data.dict()
        else:
            # Already a dict
            data_dict = dict(data)
            
        # Ensure tags is a list
        if "tags" not in data_dict or data_dict["tags"] is None:
            data_dict["tags"] = []
        
        # Add a default user_id if not provided
        # In a real application, this would come from the authenticated user
        # For now, we'll use a default UUID for testing purposes
        if "user_id" not in data_dict or data_dict["user_id"] is None:
            data_dict["user_id"] = "00000000-0000-0000-0000-000000000000"
        elif hasattr(data_dict["user_id"], "hex"):
            # If it's a UUID object, convert it to string
            data_dict["user_id"] = str(data_dict["user_id"])
            
        return data_dict
    
    def _preprocess_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tag filtering specially."""
        # Make a copy to avoid modifying the original
        processed_filters = filters.copy()
        
        # Handle tag filtering specially
        if "tag" in processed_filters:
            tag_filter = processed_filters.pop("tag")
            # Add tag filter in a way that works for all database types
            processed_filters["tags"] = tag_filter
            
        return processed_filters
        
    async def create_with_user(self, data: NoteCreate, user: User) -> Dict[str, Any]:
        """Create a new note with the user ID from the authenticated user.
        
        Args:
            data: The note data
            user: The authenticated user
            
        Returns:
            The created note
        """
        # If data is a Pydantic model, convert it to a dict first
        if hasattr(data, "model_dump"):
            # Pydantic v2
            data_dict = data.model_dump()
        elif hasattr(data, "dict"):
            # Pydantic v1
            data_dict = data.dict()
        else:
            # Already a dict
            data_dict = dict(data)
            
        # Set the user_id from the authenticated user
        # We now have the user ID from the token, but ensure it's a string
        data_dict["user_id"] = str(user.id) if hasattr(user.id, 'hex') else user.id
        
        # Use the existing create method with the updated data
        return await self.create(data_dict)
