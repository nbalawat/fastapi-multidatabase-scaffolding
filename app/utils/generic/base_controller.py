from typing import Dict, List, Optional, Any, Generic, TypeVar, Type
import logging
from typing import Dict, Any, List, Optional, Type, Generic, TypeVar
from pydantic import BaseModel
import logging

from app.utils.generic.crud import CRUDBase
from app.db.schema_registry import get_schema_registry

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)
U = TypeVar('U', bound=BaseModel)
V = TypeVar('V', bound=BaseModel)

class BaseController(Generic[T, U, V]):
    """Base controller for handling CRUD operations across different database types.
    
    Type Parameters:
        T: The create model type (e.g., NoteCreate)
        U: The update model type (e.g., NoteUpdate)
        V: The response model type (e.g., Note)
    """
    
    def __init__(self, db_adapter: CRUDBase):
        """Initialize the controller with a database adapter.
        
        Args:
            db_adapter: The database adapter to use
        """
        self.db = db_adapter
        self.schema_registry = get_schema_registry()
        
        # Get the model name from the class name
        # BaseController -> base, NotesController -> notes
        class_name = self.__class__.__name__
        if class_name.endswith('Controller'):
            self.model_name = class_name[:-10].lower()
        else:
            self.model_name = class_name.lower()
            
        # Set the collection name to the model name by default
        # This can be overridden by subclasses
        self.collection = self.model_name
            
        # Get the schema for this model and database type
        self.schema = self.schema_registry.get_schema(self.model_name, db_adapter.db_type)
        
        if not self.schema:
            logger.warning(
                f"No schema found for model {self.model_name} with database type {db_adapter.db_type}. "
                f"Some features may not work correctly."
            )
    
    async def create(self, data: Any) -> Dict[str, Any]:
        """Create a new item.
        
        Args:
            data: The item data (can be a dict or a Pydantic model)
            
        Returns:
            The created item
        """
        # Convert Pydantic model to dict if needed
        if hasattr(data, "model_dump"):
            # Pydantic v2
            data_dict = data.model_dump()
        elif hasattr(data, "dict"):
            # Pydantic v1
            data_dict = data.dict()
        else:
            # Already a dict or other type
            data_dict = data
            
        # Pre-processing hook
        processed_data = await self.before_create(data_dict)
        
        # Convert to database model if schema is available
        if self.schema:
            processed_data = self.schema.to_db_model(processed_data)
        
        # Create the item
        created_item = await self.db.create(self.collection, processed_data)
        
        # Convert from database model if schema is available
        if self.schema:
            created_item = self.schema.from_db_model(created_item)
        
        # Post-processing hook
        result = await self.after_create(created_item)
        
        return result
    
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get an item by ID.
        
        Args:
            id: The item ID
            
        Returns:
            The item or None if not found
        """
        # Get the item
        item = await self.db.read(self.collection, id)
        
        if not item:
            return None
            
        # Convert from database model if schema is available
        if self.schema:
            item = self.schema.from_db_model(item)
            
        # Post-processing hook
        result = await self.after_get(item)
        
        return result
    
    async def update(self, item_id: str, data: Any) -> Dict[str, Any]:
        """Update an item by ID.
        
        Args:
            item_id: The ID of the item to update
            data: The updated data (can be a dict or a Pydantic model)
            
        Returns:
            The updated item
        """
        # Convert Pydantic model to dict if needed
        if hasattr(data, "model_dump"):
            # Pydantic v2
            data_dict = data.model_dump()
        elif hasattr(data, "dict"):
            # Pydantic v1
            data_dict = data.dict()
        else:
            # Already a dict or other type
            data_dict = data
            
        # Pre-processing hook
        processed_data = await self.before_update(data_dict)
        
        # Convert to database model if schema is available
        if self.schema:
            processed_data = self.schema.to_db_model(processed_data)
        
        # Update the item
        updated_item = await self.db.update(self.collection, item_id, processed_data)
        
        # Convert from database model if schema is available
        if self.schema:
            updated_item = self.schema.from_db_model(updated_item)
        
        # Post-processing hook
        result = await self.after_update(updated_item)
        
        return result
    
    async def delete(self, id: str) -> bool:
        """Delete an item by ID.
        
        Args:
            id: The item ID
            
        Returns:
            True if deleted, False otherwise
        """
        # Delete the item
        result = await self.db.delete(self.collection, id)
        
        if result:
            logger.info(f"Deleted item with ID: {id}")
        else:
            logger.warning(f"Item with ID {id} not found for deletion")
            
        return result
    
    async def list(self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List items with optional filtering.
        
        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return
            filters: Optional filters
            
        Returns:
            List of items
        """
        # Pre-processing hook
        # Use the before_list hook for pre-processing
        processed_filters = await self.before_list(filters or {})
        
        # Convert filters to database model if schema is available
        if self.schema and processed_filters:
            # We don't convert the entire filters dict, just the values that match model fields
            field_names = self.schema.get_field_names()
            for field in field_names:
                if field in processed_filters:
                    # Create a temporary dict with just this field to convert it
                    temp = {field: processed_filters[field]}
                    converted = self.schema.to_db_model(temp)
                    processed_filters[field] = converted[field]
        
        # List items
        items = await self.db.list(self.collection, skip, limit, processed_filters)
        
        # Convert from database model if schema is available
        if self.schema:
            items = [self.schema.from_db_model(item) for item in items]
            
        # Post-processing hook
        result = await self.after_list(items)
        
        return result
    
    # Hook methods for subclasses to override
    
    async def before_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called before creating a record.
        
        Args:
            data: The data to process
            
        Returns:
            Processed data
        """
        return self._preprocess_create(data)
    
    async def after_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called after creating a record.
        
        Args:
            data: The data to process
            
        Returns:
            Processed data
        """
        # Convert any UUID objects to strings
        return self._convert_uuid_to_string(data)
    
    def _convert_uuid_to_string(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert any UUID objects to strings in the response data.
        
        Args:
            data: The data to process
            
        Returns:
            Data with UUID objects converted to strings
        """
        if not data:
            return data
            
        result = {}
        for key, value in data.items():
            if hasattr(value, 'hex'):  # UUID object
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = self._convert_uuid_to_string(value)
            elif isinstance(value, list):
                result[key] = [self._convert_uuid_to_string(item) if isinstance(item, dict) else 
                              str(item) if hasattr(item, 'hex') else item 
                              for item in value]
            else:
                result[key] = value
                
        return result
    
    async def before_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called before updating a record.
        
        Args:
            data: The data to process
            
        Args:
            data: The data to preprocess
            
        Returns:
            Preprocessed data
        """
        return data
    
    def _preprocess_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess data before updating a record.
        
        Args:
            data: The data to preprocess
            
        Returns:
            Preprocessed data
        """
        return data
    
    def _postprocess_read(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess data after reading a record.
        
        Args:
            data: The data to postprocess
            
        Returns:
            Postprocessed data
        """
        return data
    
    def _preprocess_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess filters before listing records.
        
        Args:
            filters: The filters to preprocess
            
        Returns:
            Preprocessed filters
        """
        return filters
        
    async def after_get(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called after getting a record.
        
        Args:
            data: The data to process
            
        Returns:
            Processed data
        """
        # Convert any UUID objects to strings
        return self._convert_uuid_to_string(data)
        
    async def after_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Hook called after listing records.
        
        Args:
            data: The data to process
            
        Returns:
            Processed data
        """
        # Convert any UUID objects to strings in each item
        return [self._convert_uuid_to_string(item) for item in data]
        
    async def after_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called after updating a record.
        
        Args:
            data: The data to process
            
        Returns:
            Processed data
        """
        # Convert any UUID objects to strings
        return self._convert_uuid_to_string(data)
        
    async def after_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called after deleting a record.
        
        Args:
            data: The data to process
            
        Returns:
            Processed data
        """
        # Convert any UUID objects to strings
        return self._convert_uuid_to_string(data)
        
    async def before_list(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-processing hook for list operations.
        
        This method can be overridden by subclasses to modify the filters
        before they are used to query the database.
        
        Args:
            filters: The filters to apply to the list operation
            
        Returns:
            The processed filters
        """
        return filters
