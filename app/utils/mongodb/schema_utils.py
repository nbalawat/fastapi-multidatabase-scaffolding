from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from uuid import uuid4
from bson import ObjectId

logger = logging.getLogger(__name__)

def prepare_mongodb_model(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a model for storage in MongoDB.
    
    Args:
        data: The model data
        
    Returns:
        The prepared data
    """
    # Create a copy to avoid modifying the original
    db_model = data.copy()
    
    # Convert string ID to ObjectId if it exists
    if "id" in db_model and isinstance(db_model["id"], str):
        # For new documents, we'll use the string ID as is
        # MongoDB driver will convert it to ObjectId
        pass
        
    # Ensure tags is a list
    if "tags" in db_model and db_model["tags"] is None:
        db_model["tags"] = []
        
    # Set timestamps
    if "created_at" not in db_model:
        db_model["created_at"] = datetime.now()
    
    # Generate ID if not present
    if "id" not in db_model:
        db_model["id"] = str(ObjectId())
        
    return db_model

def convert_from_mongodb_model(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a MongoDB model to an API model.
    
    Args:
        data: The database model data
        
    Returns:
        The API model data
    """
    # Create a copy to avoid modifying the original
    api_model = data.copy()
    
    # Convert ObjectId to string
    if "_id" in api_model:
        api_model["id"] = str(api_model["_id"])
        del api_model["_id"]
        
    # Ensure created_at and updated_at are datetime objects
    for field in ["created_at", "updated_at"]:
        if field in api_model and api_model[field] is not None and not isinstance(api_model[field], datetime):
            try:
                api_model[field] = datetime.fromisoformat(api_model[field])
            except (ValueError, TypeError):
                logger.warning(f"Could not convert {field} to datetime: {api_model[field]}")
        # If the field is None, keep it as None - this is valid for updated_at
        
    return api_model

def get_mongodb_validator_schema(fields: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a MongoDB validator schema.
    
    Args:
        fields: Dictionary of field names and their MongoDB schema definitions
        
    Returns:
        The MongoDB validator schema
    """
    properties = {}
    required = []
    
    for field_name, field_def in fields.items():
        properties[field_name] = field_def
        if field_def.get("required", False):
            required.append(field_name)
            
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": required,
            "properties": properties
        }
    }

def get_mongodb_create_collection_command(collection_name: str, validator: Dict[str, Any]) -> str:
    """Generate a MongoDB create collection command.
    
    Args:
        collection_name: The collection name
        validator: The validator schema
        
    Returns:
        The MongoDB command as a string
    """
    return f"""
    db.createCollection("{collection_name}", {{
        validator: {validator}
    }})
    """
