"""
SQL Server schema for users model.
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.db.schemas.base import BaseSchema
from app.models.users.model import UserInDB
from app.utils.sqlserver.schema_utils import prepare_sqlserver_model, convert_from_sqlserver_model, get_sqlserver_create_table_statement

logger = logging.getLogger(__name__)

class UsersSQLServerSchema(BaseSchema[UserInDB]):
    """SQL Server schema for users."""
    
    def __init__(self):
        """Initialize the schema."""
        super().__init__(model_class=UserInDB, db_type="sqlserver")
    
    def get_table_name(self) -> str:
        """Get the table name for this schema.
        
        Returns:
            The table name
        """
        return "users"
    
    def get_create_table_statement(self) -> str:
        """Get the SQL statement to create the table.
        
        Returns:
            The SQL statement
        """
        # Map model fields to SQL Server column types
        columns = {
            "id": "UNIQUEIDENTIFIER PRIMARY KEY",
            "email": "NVARCHAR(255) NOT NULL",
            "username": "NVARCHAR(255) NOT NULL",
            "hashed_password": "NVARCHAR(255) NOT NULL",
            "full_name": "NVARCHAR(255)",
            "is_active": "BIT DEFAULT 1",
            "role": "NVARCHAR(50) NOT NULL",
            "created_at": "DATETIME NOT NULL DEFAULT GETDATE()",
            "updated_at": "DATETIME"
        }
        
        # Get the base table creation statement
        table_stmt = get_sqlserver_create_table_statement(self.get_table_name(), columns)
        
        # Add unique constraints and indexes
        constraints = f"""
        -- Add unique constraints
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'UQ_users_email' AND object_id = OBJECT_ID('users'))
        ALTER TABLE users ADD CONSTRAINT UQ_users_email UNIQUE (email);
        
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'UQ_users_username' AND object_id = OBJECT_ID('users'))
        ALTER TABLE users ADD CONSTRAINT UQ_users_username UNIQUE (username);
        
        -- Create indexes
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IDX_users_role' AND object_id = OBJECT_ID('users'))
        CREATE INDEX IDX_users_role ON users(role);
        """
        
        return table_stmt + constraints
    
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
