"""
PostgreSQL schema for users model.
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.db.schemas.base import BaseSchema
from app.models.users.model import UserInDB
from app.utils.postgres.schema_utils import prepare_postgres_model, convert_from_postgres_model, get_postgres_create_table_statement
from app.utils.generic.schema_utils import map_model_to_db_columns

logger = logging.getLogger(__name__)

class UsersPostgresSchema(BaseSchema[UserInDB]):
    """PostgreSQL schema for users."""
    
    def __init__(self):
        """Initialize the schema."""
        super().__init__(model_class=UserInDB, db_type="postgres")
    
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
        # Map model fields to PostgreSQL column types
        columns = {
            "id": "UUID PRIMARY KEY",
            "email": "VARCHAR(255) UNIQUE NOT NULL",
            "username": "VARCHAR(255) UNIQUE NOT NULL",
            "hashed_password": "VARCHAR(255) NOT NULL",
            "full_name": "VARCHAR(255)",
            "is_active": "BOOLEAN DEFAULT TRUE",
            "role": "VARCHAR(50) NOT NULL",
            "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP"
        }
        
        # Add indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);"
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
