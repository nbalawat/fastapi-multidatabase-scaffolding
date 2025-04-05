"""
MongoDB schema for notes model.
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.db.schemas.base import BaseSchema
from app.models.notes.model import Note, NoteInDB
from app.utils.mongodb.schema_utils import prepare_mongodb_model, convert_from_mongodb_model, get_mongodb_validator_schema

logger = logging.getLogger(__name__)

class NotesMongoDBSchema(BaseSchema[NoteInDB]):
    """MongoDB schema for notes."""
    
    def __init__(self):
        """Initialize the schema."""
        super().__init__(model_class=NoteInDB, db_type="mongodb")
    
    def get_table_name(self) -> str:
        """Get the collection name for this schema.
        
        Returns:
            The collection name
        """
        return "notes"
    
    def get_create_table_statement(self) -> str:
        """Get the MongoDB command to create the collection.
        
        Returns:
            The MongoDB command
        """
        # Define the validator schema for MongoDB
        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["id", "title"],
                "properties": {
                    "id": {"bsonType": "string"},
                    "title": {"bsonType": "string"},
                    "content": {"bsonType": "string"},
                    "visibility": {"bsonType": "string"},
                    "tags": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"}
                    },
                    "user_id": {"bsonType": "string"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
        
        # Create the collection with validator
        return f"""
        db.createCollection("{self.get_table_name()}", {{
            validator: {validator}
        }});
        
        // Create indexes
        db.{self.get_table_name()}.createIndex({{ "title": 1 }});
        """
    
    def to_db_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert API model to database model.
        
        Args:
            data: The API model data
            
        Returns:
            The database model data
        """
        # Use the utility function for MongoDB-specific conversions
        return prepare_mongodb_model(data)
    
    def from_db_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database model to API model.
        
        Args:
            data: The database model data
            
        Returns:
            The API model data
        """
        # Use the utility function for MongoDB-specific conversions
        return convert_from_mongodb_model(data)
