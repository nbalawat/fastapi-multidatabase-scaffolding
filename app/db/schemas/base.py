from typing import Dict, Any, Type, Optional, List, TypeVar, Generic
from pydantic import BaseModel
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class BaseSchema(ABC, Generic[T]):
    """Base class for database schemas.
    
    This class defines the interface for database schemas and provides
    methods for validating and converting between database and API models.
    """
    
    def __init__(self, model_class: Type[T], db_type: str):
        """Initialize the schema.
        
        Args:
            model_class: The Pydantic model class
            db_type: The database type (postgres, sqlserver, mongodb)
        """
        self.model_class = model_class
        self.db_type = db_type
    
    @abstractmethod
    def get_table_name(self) -> str:
        """Get the table name for this schema.
        
        Returns:
            The table name
        """
        pass
    
    @abstractmethod
    def get_create_table_statement(self) -> str:
        """Get the SQL statement to create the table.
        
        Returns:
            The SQL statement
        """
        pass
    
    @abstractmethod
    def to_db_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert API model to database model.
        
        Args:
            data: The API model data
            
        Returns:
            The database model data
        """
        pass
    
    @abstractmethod
    def from_db_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database model to API model.
        
        Args:
            data: The database model data
            
        Returns:
            The API model data
        """
        pass
    
    def validate_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against the model.
        
        Args:
            data: The data to validate
            
        Returns:
            The validated data
        """
        return self.model_class(**data).dict()
    
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
