"""
Database connection management module.

This module provides a connection manager for managing database connections
across different database types.
"""
from typing import Dict, Any, Optional
import logging
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.db.base import DatabaseAdapterFactory

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Connection manager for database connections.
    
    This class manages connections to different database types and provides
    a consistent interface for getting connections.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        self.settings = get_settings()
        self.connections = {}
    
    def get_adapter(self, db_type: str):
        """Get the adapter for a specific database type without connecting.
        
        Args:
            db_type: The database type to get the adapter for
            
        Returns:
            The database adapter instance
        """
        return DatabaseAdapterFactory.get_adapter(db_type)
        
    @asynccontextmanager
    async def get_connection(self, db_type: str):
        """Get a connection to a specific database type.
        
        Args:
            db_type: The database type to connect to
            
        Yields:
            A connection to the specified database
        """
        # Get the adapter for this database type
        adapter = DatabaseAdapterFactory.get_adapter(db_type)
        
        # Connect to the database
        await adapter.connect()
        
        try:
            # Yield the connection
            yield adapter
        finally:
            # Disconnect from the database
            await adapter.disconnect()

# Create a singleton instance
connection_manager = ConnectionManager()

def get_connection_manager() -> ConnectionManager:
    """Get the connection manager instance."""
    return connection_manager
