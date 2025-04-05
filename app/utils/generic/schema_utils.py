from typing import Dict, Any, List, Optional, Type, TypeVar, Generic
import logging
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class SchemaValidator(Generic[T]):
    """Generic schema validator for Pydantic models.
    
    This class provides methods for validating data against a Pydantic model.
    """
    
    def __init__(self, model_class: Type[T]):
        """Initialize the schema validator.
        
        Args:
            model_class: The Pydantic model class
        """
        self.model_class = model_class
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against the model.
        
        Args:
            data: The data to validate
            
        Returns:
            The validated data
        """
        return self.model_class(**data).dict()
    
    def validate_partial(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate partial data against the model.
        
        This is useful for update operations where only some fields are provided.
        
        Args:
            data: The data to validate
            
        Returns:
            The validated data
        """
        # Get existing fields from the model
        model_fields = set(self.model_class.__annotations__.keys())
        
        # Only validate fields that exist in the model
        filtered_data = {k: v for k, v in data.items() if k in model_fields}
        
        # Create a partial model with only the provided fields
        return self.model_class(**filtered_data).dict(exclude_unset=True)
    
    def get_field_names(self) -> List[str]:
        """Get the field names for this model.
        
        Returns:
            The field names
        """
        return list(self.model_class.__annotations__.keys())
    
    def get_field_type(self, field_name: str) -> Optional[Type]:
        """Get the type of a field.
        
        Args:
            field_name: The field name
            
        Returns:
            The field type or None if the field doesn't exist
        """
        return self.model_class.__annotations__.get(field_name)

def generate_id() -> str:
    """Generate a unique ID.
    
    Returns:
        A unique ID
    """
    return str(uuid4())

def get_current_timestamp() -> datetime:
    """Get the current timestamp.
    
    Returns:
        The current timestamp
    """
    return datetime.now()

def prepare_base_model(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a base model with common fields.
    
    Args:
        data: The model data
        
    Returns:
        The prepared data
    """
    # Create a copy to avoid modifying the original
    db_model = data.copy()
    
    # Generate ID if not present
    if "id" not in db_model:
        db_model["id"] = generate_id()
        
    # Set timestamps
    if "created_at" not in db_model:
        db_model["created_at"] = get_current_timestamp()
        
    return db_model

def map_model_to_db_columns(model_class: Type[BaseModel], db_type: str) -> Dict[str, str]:
    """Map a Pydantic model to database columns.
    
    Args:
        model_class: The Pydantic model class
        db_type: The database type (postgres, sqlserver, mongodb)
        
    Returns:
        Dictionary of column names and their database types
    """
    # Type mapping for different databases
    type_mappings = {
        "postgres": {
            "str": "VARCHAR(255)",
            "int": "INTEGER",
            "float": "FLOAT",
            "bool": "BOOLEAN",
            "datetime": "TIMESTAMP",
            "date": "DATE",
            "time": "TIME",
            "List[str]": "TEXT[]",
            "Dict": "JSONB",
            "Any": "JSONB",
            "UUID": "UUID",
        },
        "sqlserver": {
            "str": "NVARCHAR(255)",
            "int": "INT",
            "float": "FLOAT",
            "bool": "BIT",
            "datetime": "DATETIME",
            "date": "DATE",
            "time": "TIME",
            "List[str]": "NVARCHAR(MAX)",
            "Dict": "NVARCHAR(MAX)",
            "Any": "NVARCHAR(MAX)",
            "UUID": "UNIQUEIDENTIFIER",
        },
        "mongodb": {
            # MongoDB doesn't need type mapping in the same way
            # but we'll include it for completeness
            "str": {"bsonType": "string"},
            "int": {"bsonType": "int"},
            "float": {"bsonType": "double"},
            "bool": {"bsonType": "bool"},
            "datetime": {"bsonType": "date"},
            "date": {"bsonType": "date"},
            "time": {"bsonType": "date"},
            "List[str]": {"bsonType": "array", "items": {"bsonType": "string"}},
            "Dict": {"bsonType": "object"},
            "Any": {"bsonType": "object"},
            "UUID": {"bsonType": "string"},
        }
    }
    
    # Get the type mapping for the specified database
    mapping = type_mappings.get(db_type, {})
    
    # Map model fields to database columns
    columns = {}
    for field_name, field_type in model_class.__annotations__.items():
        # Get the type name as a string
        type_name = str(field_type)
        
        # Remove Optional[] wrapper if present
        if type_name.startswith("typing.Optional["):
            type_name = type_name[16:-1]
            
        # Map the type to a database column type
        if type_name in mapping:
            columns[field_name] = mapping[type_name]
        else:
            # Default to string/varchar for unknown types
            if db_type == "postgres":
                columns[field_name] = "VARCHAR(255)"
            elif db_type == "sqlserver":
                columns[field_name] = "NVARCHAR(255)"
            elif db_type == "mongodb":
                columns[field_name] = {"bsonType": "string"}
                
    return columns
