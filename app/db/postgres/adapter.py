from typing import Any, Dict, List, Optional

from sqlalchemy import delete, insert, select, update, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.base import DatabaseAdapter, DatabaseAdapterFactory
from app.db.postgres.session import create_async_session


class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL database adapter implementation.
    
    This adapter uses SQLAlchemy Core for database operations.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the PostgreSQL adapter.
        
        Args:
            settings: Application settings containing database configuration
        """
        self.settings = settings
        self._session_factory = create_async_session(settings)
        self._session: Optional[AsyncSession] = None
    
    async def connect(self) -> None:
        """Connect to the PostgreSQL database."""
        if self._session is None:
            self._session = self._session_factory()
    
    async def disconnect(self) -> None:
        """Disconnect from the PostgreSQL database."""
        if self._session is not None:
            await self._session.close()
            self._session = None
    
    async def create(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the specified table.
        
        Args:
            collection: The name of the table
            data: The data to insert
            
        Returns:
            The created record with any generated fields (like ID)
        """
        if self._session is None:
            await self.connect()
        
        # Handle field name mappings for users table
        if collection == "users":
            # Convert is_active to disabled (they have opposite meanings)
            data_copy = data.copy()
            if "is_active" in data_copy:
                # disabled is the opposite of is_active
                data_copy["disabled"] = not data_copy["is_active"]
                del data_copy["is_active"]
            data = data_copy
        
        # Create an insert statement using raw SQL for more flexibility
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{key}" for key in data.keys())
        returning = "*"  
        
        # Build the SQL statement
        sql = f"INSERT INTO {collection} ({columns}) VALUES ({placeholders}) RETURNING {returning}"
        
        # Execute the statement
        result = await self._session.execute(text(sql), data)
        await self._session.commit()
        
        # Return the created record
        row = result.first()
        if row is not None:
            result_dict = dict(row._mapping)
            # Convert ID to string if it exists
            if 'id' in result_dict and result_dict['id'] is not None:
                result_dict['id'] = str(result_dict['id'])
                
            # Convert disabled back to is_active for users table
            if collection == "users" and "disabled" in result_dict:
                result_dict["is_active"] = not result_dict["disabled"]
                del result_dict["disabled"]
                
            return result_dict
        return {}
    
    async def read(self, collection: str, id: Any) -> Optional[Dict[str, Any]]:
        """Read a record by its ID or username.
        
        Args:
            collection: The name of the table
            id: The ID or username of the record to retrieve
            
        Returns:
            The record if found, None otherwise
        """
        if self._session is None:
            await self.connect()
        
        # Create a select statement using raw SQL
        # If id is a string and not numeric, try to find by username first
        if isinstance(id, str) and not id.isdigit():
            # Try to find by username first
            sql = f"SELECT * FROM {collection} WHERE username = :id"
            result = await self._session.execute(text(sql), {"id": id})
            row = result.first()
            
            # If not found by username, try email
            if not row and collection == "users":
                sql = f"SELECT * FROM {collection} WHERE email = :id"
                result = await self._session.execute(text(sql), {"id": id})
                row = result.first()
                
            if row:
                result_dict = dict(row._mapping)
                # Convert ID to string if it exists
                if 'id' in result_dict and result_dict['id'] is not None:
                    result_dict['id'] = str(result_dict['id'])
                    
                # Convert disabled to is_active for users table
                if collection == "users" and "disabled" in result_dict:
                    result_dict["is_active"] = not result_dict["disabled"]
                    del result_dict["disabled"]
                    
                return result_dict
            return None
        else:
            # Find by ID (numeric)
            sql = f"SELECT * FROM {collection} WHERE id = :id"
            result = await self._session.execute(text(sql), {"id": id})
            row = result.first()
            if row:
                result_dict = dict(row._mapping)
                # Convert ID to string if it exists
                if 'id' in result_dict and result_dict['id'] is not None:
                    result_dict['id'] = str(result_dict['id'])
                    
                # Convert disabled to is_active for users table
                if collection == "users" and "disabled" in result_dict:
                    result_dict["is_active"] = not result_dict["disabled"]
                    del result_dict["disabled"]
                    
                return result_dict
            return None
    
    async def update(self, collection: str, id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by its ID.
        
        Args:
            collection: The name of the table
            id: The ID of the record to update
            data: The data to update
            
        Returns:
            The updated record if found, None otherwise
        """
        if self._session is None:
            await self.connect()
        
        # Build SET clause
        set_clause = ", ".join(f"{key} = :{key}" for key in data.keys())
        
        # Create an update statement using raw SQL
        sql = f"UPDATE {collection} SET {set_clause} WHERE id = :id RETURNING *"
        
        # Add id to the parameters
        params = {**data, "id": id}
        
        # Execute the statement
        result = await self._session.execute(text(sql), params)
        await self._session.commit()
        
        # Return the updated record if found
        row = result.first()
        if row:
            result_dict = dict(row._mapping)
            # Convert ID to string if it exists
            if 'id' in result_dict and result_dict['id'] is not None:
                result_dict['id'] = str(result_dict['id'])
            return result_dict
        return None
    
    async def delete(self, collection: str, id: Any) -> bool:
        """Delete a record by its ID.
        
        Args:
            collection: The name of the table
            id: The ID of the record to delete
            
        Returns:
            True if the record was deleted, False otherwise
        """
        if self._session is None:
            await self.connect()
        
        # Create a delete statement using raw SQL
        sql = f"DELETE FROM {collection} WHERE id = :id"
        
        # Execute the statement
        result = await self._session.execute(text(sql), {"id": id})
        await self._session.commit()
        
        # Return True if a record was deleted
        return result.rowcount > 0
    
    async def list(self, collection: str, skip: int = 0, limit: int = 100, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List records from a table with pagination and optional filtering.
        
        Args:
            collection: The name of the table
            skip: Number of records to skip
            limit: Maximum number of records to return
            query: Optional dictionary of field-value pairs to filter by
            
        Returns:
            A list of records
        """
        if self._session is None:
            await self.connect()
        
        # Start building the SQL query
        sql = f"SELECT * FROM {collection}"
        params = {}
        
        # Add where clauses for each query parameter
        if query:
            where_clauses = []
            for field, value in query.items():
                where_clauses.append(f"{field} = :{field}")
                params[field] = value
            
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
        
        # Add pagination
        sql += " LIMIT :limit OFFSET :skip"
        params["limit"] = limit
        params["skip"] = skip
        
        # Execute the statement
        result = await self._session.execute(text(sql), params)
        
        # Return the records with IDs converted to strings
        records = []
        for row in result.mappings().all():
            record = dict(row)
            # Convert ID to string if it exists
            if 'id' in record and record['id'] is not None:
                record['id'] = str(record['id'])
                
            # Convert disabled to is_active for users table
            if collection == "users" and "disabled" in record:
                record["is_active"] = not record["disabled"]
                del record["disabled"]
                
            records.append(record)
        return records


# Register the PostgreSQL adapter with the factory
DatabaseAdapterFactory.register("postgres", PostgresAdapter)
