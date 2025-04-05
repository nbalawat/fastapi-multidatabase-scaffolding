from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters.
    
    This class defines the interface that all database adapters must implement,
    regardless of the underlying database technology.
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the database."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the database."""
        pass
    
    @abstractmethod
    async def create(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the specified collection.
        
        Args:
            collection: The name of the collection/table
            data: The data to insert
            
        Returns:
            The created record with any generated fields (like ID)
        """
        pass
    
    @abstractmethod
    async def read(self, collection: str, id: Any) -> Optional[Dict[str, Any]]:
        """Read a record by its ID.
        
        Args:
            collection: The name of the collection/table
            id: The ID of the record to retrieve
            
        Returns:
            The record if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, collection: str, id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by its ID.
        
        Args:
            collection: The name of the collection/table
            id: The ID of the record to update
            data: The data to update
            
        Returns:
            The updated record if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, collection: str, id: Any) -> bool:
        """Delete a record by its ID.
        
        Args:
            collection: The name of the collection/table
            id: The ID of the record to delete
            
        Returns:
            True if the record was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def list(self, collection: str, skip: int = 0, limit: int = 100, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List records from a collection with pagination and optional filtering.
        
        Args:
            collection: The name of the collection/table
            skip: Number of records to skip
            limit: Maximum number of records to return
            query: Optional dictionary of field-value pairs to filter by
            
        Returns:
            A list of records
        """
        pass


class DatabaseAdapterFactory:
    """Factory for creating database adapters.
    
    This class uses the Factory pattern to create database adapters
    based on the configured database type.
    """
    
    _adapters: Dict[str, Type[DatabaseAdapter]] = {}
    
    @classmethod
    def register(cls, db_type: str, adapter_class: Type[DatabaseAdapter]) -> None:
        """Register a database adapter class for a specific database type.
        
        Args:
            db_type: The database type identifier (e.g., "postgres", "mongodb")
            adapter_class: The adapter class to register
        """
        cls._adapters[db_type] = adapter_class
    
    @classmethod
    def get_adapter(cls, db_type: str) -> DatabaseAdapter:
        """Get an instance of the appropriate database adapter.
        
        Args:
            db_type: The database type identifier
            
        Returns:
            An instance of the requested database adapter
            
        Raises:
            ValueError: If the requested database type is not registered
        """
        if db_type not in cls._adapters:
            raise ValueError(f"No adapter registered for database type: {db_type}")
        
        # Import here to avoid circular imports
        from app.core.config import get_settings
        
        # Pass settings to the adapter constructor
        return cls._adapters[db_type](get_settings())
    
    @classmethod
    def get_registered_adapters(cls) -> List[str]:
        """Get a list of all registered database adapter types.
        
        Returns:
            A list of registered database type identifiers
        """
        return list(cls._adapters.keys())


async def get_db_adapter() -> DatabaseAdapter:
    """Get the database adapter.
    
    This function is used as a dependency in FastAPI routes.
    
    Returns:
        The database adapter for the configured database type
    """
    # Import here to avoid circular imports
    from app.core.config import get_settings
    
    # Get the configured database type
    settings = get_settings()
    db_type = settings.db_type
    
    # Get the adapter instance
    adapter = DatabaseAdapterFactory.get_adapter(db_type)
    
    # Ensure the adapter is connected
    if not hasattr(adapter, "_client") or adapter._client is None:
        await adapter.connect()
    
    return adapter
