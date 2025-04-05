"""
SQL Server schema for notes model.
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.db.schemas.base import BaseSchema
from app.models.notes.model import Note, NoteInDB
from app.utils.sqlserver.schema_utils import prepare_sqlserver_model, convert_from_sqlserver_model, get_sqlserver_create_table_statement

logger = logging.getLogger(__name__)

class NotesSQLServerSchema(BaseSchema[NoteInDB]):
    """SQL Server schema for notes."""
    
    def __init__(self):
        """Initialize the schema."""
        super().__init__(model_class=NoteInDB, db_type="sqlserver")
    
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
        # Map model fields to SQL Server column types
        columns = {
            "id": "UNIQUEIDENTIFIER PRIMARY KEY",
            "title": "NVARCHAR(255) NOT NULL",
            "content": "NVARCHAR(MAX)",
            "visibility": "NVARCHAR(50) DEFAULT 'private'",
            "tags": "NVARCHAR(MAX)",  # JSON array stored as string
            "user_id": "UNIQUEIDENTIFIER NOT NULL",
            "created_at": "DATETIME NOT NULL DEFAULT GETDATE()",
            "updated_at": "DATETIME"
        }
        
        # Get the base table creation statement
        table_stmt = get_sqlserver_create_table_statement(self.get_table_name(), columns)
        
        # Add indexes
        indexes = f"""
        -- Create indexes
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IDX_notes_title' AND object_id = OBJECT_ID('notes'))
        CREATE INDEX IDX_notes_title ON notes(title);
        """
        
        return table_stmt + indexes
    
    def to_db_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert API model to database model.
        
        Args:
            data: The API model data
            
        Returns:
            The database model data
        """
        # Use the utility function for SQL Server-specific conversions
        return prepare_sqlserver_model(data)
    
    def from_db_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database model to API model.
        
        Args:
            data: The database model data
            
        Returns:
            The API model data
        """
        # Use the utility function for SQL Server-specific conversions
        return convert_from_sqlserver_model(data)
