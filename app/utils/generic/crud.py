from typing import Any, Dict, List, Optional, TypeVar, Generic, Union
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CRUDBase(ABC):
    """Base class for CRUD operations.
    
    This abstract class defines the interface for all database adapters.
    """
    
    def __init__(self):
        """Initialize the CRUD base."""
        self.db_type = None  # Will be set by subclasses
    
    @abstractmethod
    async def connect(self):
        """Connect to the database."""
        pass
        
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the database."""
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record.
        
        Args:
            data: The data to create
            
        Returns:
            The created record
        """
        pass
    
    @abstractmethod
    async def get(self, id: Any) -> Optional[Dict[str, Any]]:
        """Get a record by ID.
        
        Args:
            id: The record ID
            
        Returns:
            The record or None if not found
        """
        pass
    
    @abstractmethod
    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record.
        
        Args:
            id: The record ID
            data: The update data
            
        Returns:
            The updated record or None if not found
        """
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete a record.
        
        Args:
            id: The record ID
            
        Returns:
            True if deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List records with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters
            
        Returns:
            List of records
        """
        pass

class GenericCRUD(CRUDBase, Generic[T]):
    """Generic CRUD operations that can be used across models.
    
    This class implements the CRUDBase interface and provides a generic implementation
    that can be used with any model type.
    """
    
    def __init__(self, db_adapter=None):
        """Initialize the CRUD base with an optional database adapter.
        
        Args:
            db_adapter: The database adapter to use
        """
        super().__init__()
        self.db_adapter = db_adapter
        self.db_type = getattr(db_adapter, 'db_type', None)
    
    async def connect(self) -> None:
        """Connect to the database."""
        if self.db_adapter and hasattr(self.db_adapter, 'connect'):
            await self.db_adapter.connect()
        else:
            logger.warning("No database adapter provided or adapter does not support connect()")
    
    async def disconnect(self) -> None:
        """Disconnect from the database."""
        if self.db_adapter and hasattr(self.db_adapter, 'disconnect'):
            await self.db_adapter.disconnect()
        else:
            logger.warning("No database adapter provided or adapter does not support disconnect()")
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record.
        
        Args:
            data: The data to create
            
        Returns:
            The created record
        """
        if self.db_adapter and hasattr(self.db_adapter, 'create'):
            collection = self._get_collection_name()
            return await self.db_adapter.create(collection, data)
        else:
            logger.error("No database adapter provided or adapter does not support create()")
            return {}
    
    async def get(self, id: Any) -> Optional[Dict[str, Any]]:
        """Get a record by ID.
        
        Args:
            id: The record ID
            
        Returns:
            The record or None if not found
        """
        if self.db_adapter and hasattr(self.db_adapter, 'read'):
            collection = self._get_collection_name()
            return await self.db_adapter.read(collection, id)
        else:
            logger.error("No database adapter provided or adapter does not support read()")
            return None
    
    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record.
        
        Args:
            id: The record ID
            data: The update data
            
        Returns:
            The updated record or None if not found
        """
        if self.db_adapter and hasattr(self.db_adapter, 'update'):
            collection = self._get_collection_name()
            return await self.db_adapter.update(collection, id, data)
        else:
            logger.error("No database adapter provided or adapter does not support update()")
            return None
    
    async def delete(self, id: Any) -> bool:
        """Delete a record.
        
        Args:
            id: The record ID
            
        Returns:
            True if deleted, False otherwise
        """
        if self.db_adapter and hasattr(self.db_adapter, 'delete'):
            collection = self._get_collection_name()
            return await self.db_adapter.delete(collection, id)
        else:
            logger.error("No database adapter provided or adapter does not support delete()")
            return False
    
    async def list(self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List records with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters
            
        Returns:
            List of records
        """
        if self.db_adapter and hasattr(self.db_adapter, 'list'):
            collection = self._get_collection_name()
            prepared_filters = self.prepare_filters(filters)
            return await self.db_adapter.list(collection, skip, limit, prepared_filters)
        else:
            logger.error("No database adapter provided or adapter does not support list()")
            return []
    
    def _get_collection_name(self) -> str:
        """Get the collection name based on the class name.
        
        Returns:
            The collection name
        """
        class_name = self.__class__.__name__
        if class_name.endswith('CRUD'):
            return class_name[:-4].lower()
        return class_name.lower()
    
    @staticmethod
    def prepare_filters(query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare filters for database queries.
        
        Args:
            query: Optional dictionary of field-value pairs to filter by
            
        Returns:
            Prepared filters dictionary
        """
        if not query:
            return {}
            
        # Convert UUID objects to strings
        filters = {}
        for key, value in query.items():
            if isinstance(value, UUID):
                filters[key] = str(value)
            else:
                filters[key] = value
                
        return filters
    
    @staticmethod
    def handle_id_conversion(id_value: Any) -> Union[str, int]:
        """Convert ID to appropriate type based on value.
        
        Args:
            id_value: The ID value to convert
            
        Returns:
            Converted ID as string or int
        """
        if isinstance(id_value, str) and id_value.isdigit():
            return int(id_value)
        return id_value
    
    @staticmethod
    def format_response(record: Dict[str, Any]) -> Dict[str, Any]:
        """Format database record for API response.
        
        Args:
            record: The database record to format
            
        Returns:
            Formatted record
        """
        if not record:
            return {}
            
        # Ensure ID is a string
        if 'id' in record and record['id'] is not None:
            record['id'] = str(record['id'])
            
        return record
