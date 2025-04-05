"""
PostgreSQL schema for notes model.
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.db.schemas.base import BaseSchema
from app.models.notes.model import Note, NoteInDB
from app.utils.postgres.schema_utils import prepare_postgres_model, convert_from_postgres_model, get_postgres_create_table_statement

logger = logging.getLogger(__name__)

class NotesPostgresSchema(BaseSchema[NoteInDB]):
    """PostgreSQL schema for notes."""
    
    def __init__(self):
        """Initialize the schema."""
        super().__init__(model_class=NoteInDB, db_type="postgres")
    
    def get_table_name(self) -> str:
        """Get the table name for this schema.
        
        Returns:
            The table name
        """
        return "notes"
    
    def get_create_table_statement(self) -> str:
        """Get the SQL statement to create the table.
        
        Returns:
            The SQL statement
        """
        # Map model fields to PostgreSQL column types
        columns = {
            "id": "UUID PRIMARY KEY",
            "title": "VARCHAR(255) NOT NULL",
            "content": "TEXT",
            "visibility": "VARCHAR(50) DEFAULT 'private'",
            "tags": "TEXT[]",
            "user_id": "UUID NOT NULL",
            "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP"
        }
        
        # Add indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title);",
        ]
        
        # Get the base table creation statement
        table_stmt = get_postgres_create_table_statement(self.get_table_name(), columns)
        
        # Combine with indexes
        return table_stmt + "\n" + "\n".join(indexes)
    
    def to_db_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert API model to database model.
        
        Args:
            data: The API model data
            
        Returns:
            The database model data
        """
        # Use the utility function for PostgreSQL-specific conversions
        return prepare_postgres_model(data)
    
    def from_db_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database model to API model.
        
        Args:
            data: The database model data
            
        Returns:
            The API model data
        """
        # Use the utility function for PostgreSQL-specific conversions
        return convert_from_postgres_model(data)
