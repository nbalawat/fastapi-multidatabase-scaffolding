"""
Database adapters module.

This module contains implementations of the DatabaseAdapter interface for different database types.
All adapter classes are registered with the DatabaseAdapterFactory on import.
"""
from typing import Dict, Any, List, Optional
import logging
import asyncio
from uuid import UUID

# Import base adapter classes
from app.db.base import DatabaseAdapter, DatabaseAdapterFactory
from app.core.config import Settings

logger = logging.getLogger(__name__)

class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL database adapter."""
    
    def __init__(self, settings: Settings):
        """Initialize the adapter with settings.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.db_type = "postgres"
        self._client = None
        
    async def connect(self) -> None:
        """Connect to the PostgreSQL database."""
        import asyncpg
        
        if self._client is None:
            try:
                # Build connection string from individual settings
                conn_str = f"postgresql://{self.settings.db_user}:{self.settings.db_password}@{self.settings.db_host}:{self.settings.db_port}/{self.settings.db_name}"
                
                logger.info(f"Connecting to PostgreSQL at {self.settings.db_host}:{self.settings.db_port}")
                self._client = await asyncpg.connect(conn_str)
                logger.info("Connected to PostgreSQL database")
            except Exception as e:
                logger.error(f"Error connecting to PostgreSQL database: {e}")
                raise
                
    async def execute(self, query: str, *args, **kwargs) -> None:
        """Execute a query on the PostgreSQL database.
        
        Args:
            query: The query to execute
            *args: Positional arguments for the query
            **kwargs: Keyword arguments for the query
        """
        if self._client is None:
            raise ValueError("Not connected to PostgreSQL database")
            
        try:
            await self._client.execute(query, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing query on PostgreSQL database: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from the PostgreSQL database."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from PostgreSQL database")
    
    async def create(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the specified collection.
        
        Args:
            collection: The name of the table
            data: The data to insert
            
        Returns:
            The created record with any generated fields
        """
        # Build the SQL query
        fields = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(fields))]
        values = [data[field] for field in fields]
        
        query = f"""
        INSERT INTO {collection} ({', '.join(fields)})
        VALUES ({', '.join(placeholders)})
        RETURNING *
        """
        
        # Execute the query
        result = await self._client.fetchrow(query, *values)
        
        # Convert the result to a dictionary
        return dict(result) if result else None
    
    async def read(self, collection: str, id_or_key: Any, field: str = "id") -> Optional[Dict[str, Any]]:
        """Read a record by its ID or another field.
        
        Args:
            collection: The name of the table
            id_or_key: The value to search for
            field: The field to search on (default: 'id')
            
        Returns:
            The record if found, None otherwise
        """
        query = f"SELECT * FROM {collection} WHERE {field} = $1"
        try:
            logger.debug(f"Executing query: {query} with value: {id_or_key}")
            result = await self._client.fetchrow(query, id_or_key)
            
            if result:
                # Convert the result to a dictionary
                result_dict = dict(result)
                
                # Get the schema for this model if available
                from app.db.schema_registry import get_schema_registry
                schema_registry = get_schema_registry()
                schema = schema_registry.get_schema(collection, "postgres")
                
                # Apply schema conversion if schema exists
                if schema:
                    return schema.from_db_model(result_dict)
                else:
                    # Apply basic conversion for UUID objects
                    from app.utils.postgres.schema_utils import convert_from_postgres_model
                    return convert_from_postgres_model(result_dict)
            return None
        except Exception as e:
            logger.error(f"Error reading from {collection} with {field}={id_or_key}: {e}")
            # If the error is related to UUID conversion, try with a different approach
            if 'invalid UUID' in str(e) and field == 'id':
                # Try with a string comparison instead
                try:
                    query = f"SELECT * FROM {collection} WHERE {field}::text = $1"
                    logger.debug(f"Retrying with string comparison: {query}")
                    result = await self._client.fetchrow(query, str(id_or_key))
                    return dict(result) if result else None
                except Exception as retry_error:
                    logger.error(f"Error on retry: {retry_error}")
            raise
    
    async def update(self, collection: str, id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by its ID.
        
        Args:
            collection: The name of the table
            id: The ID of the record to update
            data: The data to update
            
        Returns:
            The updated record if found, None otherwise
        """
        # Build the SET clause
        fields = list(data.keys())
        set_clause = ", ".join([f"{field} = ${i+2}" for i, field in enumerate(fields)])
        values = [data[field] for field in fields]
        
        query = f"""
        UPDATE {collection}
        SET {set_clause}
        WHERE id = $1
        RETURNING *
        """
        
        # Execute the query
        result = await self._client.fetchrow(query, id, *values)
        
        # Convert the result to a dictionary
        return dict(result) if result else None
    
    async def delete(self, collection: str, id: Any) -> bool:
        """Delete a record by its ID.
        
        Args:
            collection: The name of the table
            id: The ID of the record to delete
            
        Returns:
            True if the record was deleted, False otherwise
        """
        query = f"DELETE FROM {collection} WHERE id = $1 RETURNING id"
        result = await self._client.fetchval(query, id)
        return result is not None
    
    async def list(self, collection: str, skip: int = 0, limit: int = 100, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List records from a collection with pagination and optional filtering.
        
        Args:
            collection: The name of the table
            skip: Number of records to skip
            limit: Maximum number of records to return
            query: Optional dictionary of field-value pairs to filter by
            
        Returns:
            A list of records
        """
        # Build the WHERE clause if query is provided
        where_clause = ""
        values = []
        
        if query:
            conditions = []
            for i, (field, value) in enumerate(query.items()):
                conditions.append(f"{field} = ${i+1}")
                values.append(value)
            
            if conditions:
                where_clause = f"WHERE {' AND '.join(conditions)}"
        
        # Build the SQL query
        sql_query = f"""
        SELECT * FROM {collection}
        {where_clause}
        ORDER BY id
        LIMIT {limit} OFFSET {skip}
        """
        
        # Execute the query
        results = await self._client.fetch(sql_query, *values)
        
        # Convert the results to dictionaries
        return [dict(row) for row in results]


class MongoDBAdapter(DatabaseAdapter):
    """MongoDB database adapter."""
    
    def __init__(self, settings: Settings):
        """Initialize the adapter with settings.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.db_type = "mongodb"
        self._client = None
        self._db = None
    
    async def connect(self) -> None:
        """Connect to the MongoDB database."""
        from motor.motor_asyncio import AsyncIOMotorClient
        import socket
        import time
        
        if self._client is None:
            # Set up connection parameters
            max_retries = 5
            retry_delay = 3  # seconds
            attempt = 0
            last_error = None
            
            while attempt < max_retries:
                try:
                    # Try to resolve hostname first if we're in Docker
                    if self.settings.use_docker and not self.settings.mongodb_connection_string:
                        try:
                            # Try to resolve the MongoDB hostname
                            logger.info(f"Attempting to resolve MongoDB hostname: {self.settings.db_host}")
                            resolved_ip = socket.gethostbyname(self.settings.db_host)
                            logger.info(f"Resolved MongoDB hostname to IP: {resolved_ip}")
                            
                            # Use the resolved IP instead of hostname
                            conn_str = f"mongodb://{self.settings.db_user}:{self.settings.db_password}@{resolved_ip}:{self.settings.db_port}/{self.settings.db_name}?authSource=admin"
                        except socket.gaierror:
                            logger.warning(f"Could not resolve MongoDB hostname: {self.settings.db_host}, trying alternatives")
                            
                            # Try alternative hostnames for Docker environments
                            if self.settings.db_host == "mongodb":
                                # Try localhost as fallback
                                conn_str = f"mongodb://{self.settings.db_user}:{self.settings.db_password}@host.docker.internal:{self.settings.db_port}/{self.settings.db_name}?authSource=admin"
                                logger.info("Trying host.docker.internal as alternative")
                            else:
                                # Use the connection string as provided
                                conn_str = f"mongodb://{self.settings.db_user}:{self.settings.db_password}@{self.settings.db_host}:{self.settings.db_port}/{self.settings.db_name}?authSource=admin"
                    elif self.settings.mongodb_connection_string:
                        # Use the explicit connection string if provided
                        conn_str = self.settings.mongodb_connection_string
                    else:
                        # Build a standard MongoDB connection string with authSource=admin
                        conn_str = f"mongodb://{self.settings.db_user}:{self.settings.db_password}@{self.settings.db_host}:{self.settings.db_port}/{self.settings.db_name}?authSource=admin"
                    
                    logger.info(f"Connecting to MongoDB (attempt {attempt+1}/{max_retries}) using: {conn_str.replace(self.settings.db_password, '****')}")
                    
                    # Increase timeout for Docker environments
                    self._client = AsyncIOMotorClient(
                        conn_str, 
                        serverSelectionTimeoutMS=10000,
                        connectTimeoutMS=10000,
                        socketTimeoutMS=10000
                    )
                    
                    # Verify connection by checking server info
                    await self._client.admin.command('ping')
                    self._db = self._client[self.settings.db_name]
                    logger.info("Connected to MongoDB database successfully")
                    return
                    
                except Exception as e:
                    last_error = e
                    logger.warning(f"MongoDB connection attempt {attempt+1}/{max_retries} failed: {e}")
                    attempt += 1
                    if attempt < max_retries:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
            
            # If we get here, all retries failed
            logger.error(f"Failed to connect to MongoDB after {max_retries} attempts. Last error: {last_error}")
            raise last_error
    
    async def disconnect(self) -> None:
        """Disconnect from the MongoDB database."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Disconnected from MongoDB database")
    
    async def create(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the specified collection.
        
        Args:
            collection: The name of the collection
            data: The data to insert
            
        Returns:
            The created record with any generated fields
        """
        result = await self._db[collection].insert_one(data)
        if result.inserted_id:
            return await self.read(collection, data["id"])
        return None
    
    async def read(self, collection: str, id_or_key: Any, field: str = "id") -> Optional[Dict[str, Any]]:
        """Read a record by its ID or another field.
        
        Args:
            collection: The name of the collection
            id_or_key: The value to search for
            field: The field to search on (default: 'id')
            
        Returns:
            The record if found, None otherwise
        """
        try:
            logger.debug(f"Finding document in {collection} where {field}={id_or_key}")
            result = await self._db[collection].find_one({field: id_or_key})
            return result
        except Exception as e:
            logger.error(f"Error reading from {collection} with {field}={id_or_key}: {e}")
            raise
    
    async def update(self, collection: str, id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by its ID.
        
        Args:
            collection: The name of the collection
            id: The ID of the record to update
            data: The data to update
            
        Returns:
            The updated record if found, None otherwise
        """
        result = await self._db[collection].update_one(
            {"id": id},
            {"$set": data}
        )
        
        if result.modified_count > 0:
            return await self.read(collection, id)
        return None
    
    async def delete(self, collection: str, id: Any) -> bool:
        """Delete a record by its ID.
        
        Args:
            collection: The name of the collection
            id: The ID of the record to delete
            
        Returns:
            True if the record was deleted, False otherwise
        """
        result = await self._db[collection].delete_one({"id": id})
        return result.deleted_count > 0
    
    async def list(self, collection: str, skip: int = 0, limit: int = 100, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List records from a collection with pagination and optional filtering.
        
        Args:
            collection: The name of the collection
            skip: Number of records to skip
            limit: Maximum number of records to return
            query: Optional dictionary of field-value pairs to filter by
            
        Returns:
            A list of records
        """
        cursor = self._db[collection].find(query or {}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)


class SQLServerAdapter(DatabaseAdapter):
    """SQL Server database adapter."""
    
    def __init__(self, settings: Settings):
        """Initialize the adapter with settings.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.db_type = "sqlserver"
        self._connection = None
    
    async def connect(self) -> None:
        """Connect to the SQL Server database."""
        try:
            import aioodbc
        except ImportError:
            logger.error("aioodbc module not installed. SQL Server functionality will not be available.")
            logger.error("To use SQL Server, install aioodbc package with: pip install aioodbc")
            # Set a flag to indicate the adapter is not available
            self._not_available = True
            return
        
        if self._connection is None:
            try:
                # Build connection string for SQL Server
                # Try different driver names to improve compatibility
                drivers = [
                    "ODBC Driver 17 for SQL Server",
                    "FreeTDS",
                    "TDS"
                ]
                
                # Try to connect with each driver
                for driver in drivers:
                    try:
                        # First connect to master database
                        master_conn_str = (
                            f"DRIVER={{{driver}}};SERVER={self.settings.db_host},{self.settings.db_port};" 
                            f"DATABASE=master;UID={self.settings.db_user};PWD={self.settings.db_password}"
                        )
                        
                        logger.info(f"Attempting to connect to master database with driver: {driver}")
                        master_conn = await aioodbc.connect(dsn=master_conn_str)
                        
                        # Check if our database exists and create it if it doesn't
                        async with await master_conn.cursor() as cursor:
                            # Check if database exists
                            check_db_query = f"SELECT database_id FROM sys.databases WHERE name = '{self.settings.db_name}'"
                            await cursor.execute(check_db_query)
                            row = await cursor.fetchone()
                            
                            if not row:
                                # Database doesn't exist, create it
                                logger.info(f"Database {self.settings.db_name} does not exist, creating it...")
                                create_db_query = f"CREATE DATABASE {self.settings.db_name}"
                                await cursor.execute(create_db_query)
                                logger.info(f"Database {self.settings.db_name} created successfully")
                        
                        # Close master connection
                        await master_conn.close()
                        
                        # Now connect to our database
                        conn_str = (
                            f"DRIVER={{{driver}}};SERVER={self.settings.db_host},{self.settings.db_port};" 
                            f"DATABASE={self.settings.db_name};UID={self.settings.db_user};PWD={self.settings.db_password};" 
                            f"TrustServerCertificate=yes;MultipleActiveResultSets=True"
                        )
                        
                        logger.info(f"Attempting to connect to {self.settings.db_name} with driver: {driver}")
                        self._connection = await aioodbc.connect(dsn=conn_str, autocommit=True)
                        logger.info(f"Successfully connected using driver: {driver}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed with driver {driver}: {e}")
                
                # If no connection was established, raise an exception
                if self._connection is None:
                    raise Exception("Failed to connect with any available ODBC driver")
                
                logger.info(f"Connected to SQL Server at {self.settings.db_host}:{self.settings.db_port}")
            except Exception as e:
                logger.error(f"Error connecting to SQL Server database: {e}")
                # Don't raise the exception, just log it and mark the adapter as not available
                self._not_available = True
    
    async def disconnect(self) -> None:
        """Disconnect from the SQL Server database."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Disconnected from SQL Server database")
    
    async def cursor(self):
        """Get a cursor for executing SQL queries.
        
        Returns:
            A database cursor
            
        Raises:
            Exception: If the connection is not established
        """
        if not self._connection:
            await self.connect()
            if not self._connection:
                raise Exception("Failed to establish database connection")
        
        return await self._connection.cursor()
    
    async def create(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the specified collection.
        
        Args:
            collection: The name of the table
            data: The data to insert
            
        Returns:
            The created record with any generated fields
        """
        # Build the SQL query
        fields = list(data.keys())
        
        # Special handling for UUIDs in SQL Server
        placeholders = []
        values = []
        
        for field in fields:
            value = data[field]
            # Handle UUIDs specially for SQL Server
            if field == "id" and isinstance(value, str):
                # Use CAST for UUID values
                placeholders.append(f"CAST(? AS UNIQUEIDENTIFIER)")
            else:
                placeholders.append("?")
            values.append(value)
        
        # For SQL Server, we need to use OUTPUT clause to get inserted values
        # since SCOPE_IDENTITY() only works for identity columns
        query = f"""
        INSERT INTO {collection} ({', '.join(fields)})
        OUTPUT INSERTED.*
        VALUES ({', '.join(placeholders)});
        """
        
        # Execute the query
        async with await self.cursor() as c:
            await c.execute(query, values)
            row = await c.fetchone()
            
            if not row:
                return None
                
            # Get column names
            columns = [column[0] for column in c.description]
            
            # Convert the row to a dictionary
            return dict(zip(columns, row))
    
    async def read(self, collection: str, id_or_key: Any, field: str = "id") -> Optional[Dict[str, Any]]:
        """Read a record by its ID or another field.
        
        Args:
            collection: The name of the table
            id_or_key: The value to search for
            field: The field to search on (default: 'id')
            
        Returns:
            The record if found, None otherwise
        """
        # Special handling for UUID fields in SQL Server
        if field == "id" and isinstance(id_or_key, str):
            # For SQL Server, we need to cast string UUIDs to UNIQUEIDENTIFIER
            query = f"SELECT * FROM {collection} WHERE {field} = CAST(? AS UNIQUEIDENTIFIER)"
        else:
            query = f"SELECT * FROM {collection} WHERE {field} = ?"
        
        try:
            async with await self.cursor() as c:
                logger.debug(f"Executing query: {query} with value: {id_or_key}")
                await c.execute(query, [id_or_key])
                row = await c.fetchone()
                
                if not row:
                    return None
                    
                # Get column names
                columns = [column[0] for column in c.description]
                
                # Convert the row to a dictionary
                return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Error reading from {collection} with {field}={id_or_key}: {e}")
            raise
    
    async def update(self, collection: str, id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by its ID.
        
        Args:
            collection: The name of the table
            id: The ID of the record to update
            data: The data to update
            
        Returns:
            The updated record if found, None otherwise
        """
        # Build the SET clause
        fields = list(data.keys())
        set_clause = ", ".join([f"{field} = ?" for field in fields])
        values = [data[field] for field in fields]
        
        # Special handling for UUID fields in SQL Server
        if isinstance(id, str):
            # For SQL Server, we need to cast string UUIDs to UNIQUEIDENTIFIER
            query = f"""
            UPDATE {collection}
            SET {set_clause}
            WHERE id = CAST(? AS UNIQUEIDENTIFIER);
            SELECT * FROM {collection} WHERE id = CAST(? AS UNIQUEIDENTIFIER);
            """
        else:
            query = f"""
            UPDATE {collection}
            SET {set_clause}
            WHERE id = ?;
            SELECT * FROM {collection} WHERE id = ?;
            """
        
        # Execute the query
        async with await self.cursor() as c:
            await c.execute(query, values + [id, id])
            row = await c.fetchone()
            
            if not row:
                return None
                
            # Get column names
            columns = [column[0] for column in c.description]
            
            # Convert the row to a dictionary
            return dict(zip(columns, row))
    
    async def delete(self, collection: str, id: Any) -> bool:
        """Delete a record by its ID.
        
        Args:
            collection: The name of the table
            id: The ID of the record to delete
            
        Returns:
            True if the record was deleted, False otherwise
        """
        # Special handling for UUID fields in SQL Server
        if isinstance(id, str):
            # For SQL Server, we need to cast string UUIDs to UNIQUEIDENTIFIER
            query = f"DELETE FROM {collection} WHERE id = CAST(? AS UNIQUEIDENTIFIER)"
        else:
            query = f"DELETE FROM {collection} WHERE id = ?"
        
        async with await self.cursor() as c:
            await c.execute(query, [id])
            return c.rowcount > 0
    
    async def list(self, collection: str, skip: int = 0, limit: int = 100, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List records from a collection with pagination and optional filtering.
        
        Args:
            collection: The name of the table
            skip: Number of records to skip
            limit: Maximum number of records to return
            query: Optional dictionary of field-value pairs to filter by
            
        Returns:
            A list of records
        """
        # Build the WHERE clause if query is provided
        where_clause = ""
        values = []
        
        if query:
            conditions = []
            for field, value in query.items():
                # Special handling for UUID fields in SQL Server
                if field == "id" and isinstance(value, str):
                    conditions.append(f"{field} = CAST(? AS UNIQUEIDENTIFIER)")
                else:
                    conditions.append(f"{field} = ?")
                values.append(value)
            
            if conditions:
                where_clause = f"WHERE {' AND '.join(conditions)}"
        
        # Build the SQL query
        sql_query = f"""
        SELECT * FROM {collection}
        {where_clause}
        ORDER BY id
        OFFSET {skip} ROWS
        FETCH NEXT {limit} ROWS ONLY
        """
        
        # Execute the query
        async with await self.cursor() as c:
            await c.execute(sql_query, values)
            rows = await c.fetchall()
            
            if not rows:
                return []
                
            # Get column names
            columns = [column[0] for column in c.description]
            
            # Convert the rows to dictionaries
            return [dict(zip(columns, row)) for row in rows]


# Register all adapters with the factory
DatabaseAdapterFactory.register("postgres", PostgresAdapter)
DatabaseAdapterFactory.register("mongodb", MongoDBAdapter)
DatabaseAdapterFactory.register("sqlserver", SQLServerAdapter)
