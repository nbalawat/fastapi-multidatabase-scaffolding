from typing import Dict, Any, List, Optional
import logging
import asyncio
from contextlib import asynccontextmanager

from app.db.schema_registry import get_schema_registry
from app.db.connections import get_connection_manager
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Database initializer for creating tables and collections.
    
    This class handles the initialization of database schemas for all
    supported database types.
    """
    
    def __init__(self):
        """Initialize the database initializer."""
        self.schema_registry = get_schema_registry()
        self.connection_manager = get_connection_manager()
        self.settings = get_settings()
    
    async def initialize_all_databases(self):
        """Initialize only the primary database type configured for this container."""
        logger.info("Initializing database")
        
        # Only initialize the primary database type specified in settings
        primary_db_type = self.settings.db_type
        logger.info(f"Primary database type: {primary_db_type}")
        
        # Initialize only the primary database
        await self.initialize_database(primary_db_type)
    
    async def initialize_database(self, db_type: str):
        """Initialize a specific database type.
        
        Args:
            db_type: The database type to initialize
        """
        logger.info(f"Initializing {db_type} database")
        
        # Check if the adapter is available
        try:
            # Get a connection to check availability
            adapter = self.connection_manager.get_adapter(db_type)
            
            # Skip if adapter is marked as not available (e.g., missing dependencies)
            if hasattr(adapter, '_not_available') and adapter._not_available:
                logger.warning(f"Skipping {db_type} initialization as the adapter is not available")
                return
                
            # Get create table statements for this database type
            create_statements = self.schema_registry.get_create_table_statements(db_type)
            
            if not create_statements:
                logger.warning(f"No schemas found for {db_type}")
                return
                
            # Execute create table statements
            if db_type in ["postgres", "sqlserver"]:
                await self._initialize_sql_database(db_type, create_statements)
            elif db_type == "mongodb":
                await self._initialize_mongodb(create_statements)
            else:
                logger.warning(f"Unsupported database type: {db_type}")
                
        except Exception as e:
            logger.error(f"Error initializing {db_type} database: {e}")
    
    async def _initialize_sql_database(self, db_type: str, create_statements: Dict[str, str]):
        """Initialize a SQL database.
        
        Args:
            db_type: The database type
            create_statements: Dictionary of create table statements
        """
        # Get a connection
        async with self.connection_manager.get_connection(db_type) as conn:
            # Execute each create statement
            for model_name, statement in create_statements.items():
                try:
                    logger.info(f"Creating table for {model_name} in {db_type}")
                    
                    # Handle different database types
                    if db_type == "postgres":
                        # PostgreSQL uses execute on the connection directly
                        await conn.execute(statement)
                    elif db_type == "sqlserver":
                        # SQL Server uses a cursor
                        # We need to await the cursor method first
                        cursor = await conn.cursor()
                        async with cursor as c:
                            await c.execute(statement)
                    else:
                        logger.warning(f"Unsupported SQL database type for execution: {db_type}")
                        
                except Exception as e:
                    logger.error(f"Error creating table for {model_name} in {db_type}: {e}")
    
    async def _initialize_mongodb(self, create_statements: Dict[str, str]):
        """Initialize MongoDB collections.
        
        Args:
            create_statements: Dictionary of create collection statements
        """
        # For MongoDB, we need to parse the statements and execute them
        # This is a simplified version that just creates collections
        async with self.connection_manager.get_connection("mongodb") as client:
            # The MongoDB adapter already has the database connection set up
            # We don't need to access it using dictionary-style access
            # Instead, use the _db attribute directly
            db = client._db
            
            logger.info(f"Initializing MongoDB collections in database '{db.name}'")
            
            for model_name, _ in create_statements.items():
                try:
                    logger.info(f"Creating collection for {model_name} in MongoDB")
                    # Just create the collection if it doesn't exist
                    # We're not using the validator schema for simplicity
                    if model_name not in await db.list_collection_names():
                        await db.create_collection(model_name)
                except Exception as e:
                    logger.error(f"Error creating collection for {model_name} in MongoDB: {e}")

# Create a singleton instance
db_initializer = DatabaseInitializer()

def get_db_initializer() -> DatabaseInitializer:
    """Get the database initializer instance."""
    return db_initializer

@asynccontextmanager
async def initialize_databases():
    """Context manager for initializing databases on application startup."""
    initializer = get_db_initializer()
    await initializer.initialize_all_databases()
    yield
