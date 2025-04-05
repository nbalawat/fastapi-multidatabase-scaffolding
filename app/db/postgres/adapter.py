from typing import Any, Dict, List, Optional, Union, Set
import logging
import json

from sqlalchemy import delete, insert, select, update, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.base import DatabaseAdapter, DatabaseAdapterFactory
from app.db.postgres.session import create_async_session

logger = logging.getLogger(__name__)

# Helper functions for PostgreSQL adapter
def parse_postgres_array(value: Any, field_name: str = "unknown") -> List[Any]:
    """Parse a PostgreSQL array format into a Python list with error handling.
    
    Args:
        value: The PostgreSQL array to parse (could be a string like '{item1,item2}' or already a list)
        field_name: The name of the field being parsed (for logging)
        
    Returns:
        The parsed list or an empty list if parsing fails
    """
    logger.info(f"Parsing PostgreSQL array for {field_name}: {value}")
    
    # If it's already a list, return it
    if isinstance(value, list):
        return value
        
    # If it's None or empty, return an empty list
    if value is None or (isinstance(value, str) and not value.strip()):
        return []
    
    # If it's a string in PostgreSQL array format {item1,item2}
    if isinstance(value, str):
        try:
            # Try to parse as JSON first (in case it's a JSON string)
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    logger.info(f"Successfully parsed {field_name} as JSON: {parsed}")
                    return parsed
            except json.JSONDecodeError:
                # Not JSON, continue with PostgreSQL array parsing
                pass
                
            # Handle PostgreSQL array format
            if value.startswith('{') and value.endswith('}'):
                # Remove braces and split by comma
                items = value[1:-1].split(',') if value != '{}' else []
                # Clean up items (remove quotes, etc.)
                cleaned_items = [item.strip('"\' ') for item in items if item.strip()]
                logger.info(f"Successfully parsed {field_name} from PostgreSQL array: {cleaned_items}")
                return cleaned_items
            elif ',' in value:
                # Maybe it's just a comma-separated string
                items = [item.strip() for item in value.split(',') if item.strip()]
                logger.info(f"Parsed {field_name} as comma-separated string: {items}")
                return items
            else:
                # Single value, return as a list with one item
                logger.info(f"Treating {field_name} as single value: {value}")
                return [value]
        except Exception as e:
            logger.error(f"Error parsing {field_name}: {e}, raw value: {value}")
    
    # For any other type, try to convert to string and parse
    try:
        str_value = str(value)
        if str_value:
            logger.info(f"Converting {field_name} to string and parsing: {str_value}")
            return [str_value]
    except Exception as e:
        logger.error(f"Error converting {field_name} to string: {e}")
    
    # Return empty list as fallback
    return []


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
        
        # Handle different collection types
        if collection == "notes":
            # Create a copy of the data to avoid modifying the original
            insert_data = data.copy()
            
            # Handle tags array if present
            if "tags" in insert_data and isinstance(insert_data["tags"], list):
                # No need to modify tags as PostgreSQL can handle arrays in parameters
                pass
            
            # Create an insert statement using raw SQL
            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join(f":{key}" for key in insert_data.keys())
            sql = f"INSERT INTO {collection} ({columns}) VALUES ({placeholders}) RETURNING *"
            
            # Execute the statement
            result = await self._session.execute(text(sql), insert_data)
            await self._session.commit()
            
            # Get the inserted record
            row = result.mappings().first()
            if row:
                result_dict = dict(row)
                # Convert ID to string if it exists
                if 'id' in result_dict and result_dict['id'] is not None:
                    result_dict['id'] = str(result_dict['id'])
                
                # Handle tags array in the result
                if 'tags' in result_dict:
                    result_dict['tags'] = parse_postgres_array(result_dict['tags'], field_name='tags')
                    logger.info(f"Parsed tags in create method: {result_dict['tags']}")
                
                return result_dict
            return {}
        else:
            # Standard handling for other collections
            # Create a copy of the data to avoid modifying the original
            insert_data = data.copy()
            
            # Create an insert statement using raw SQL
            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join(f":{key}" for key in insert_data.keys())
            sql = f"INSERT INTO {collection} ({columns}) VALUES ({placeholders}) RETURNING *"
            
            # Execute the statement
            result = await self._session.execute(text(sql), insert_data)
            await self._session.commit()
            
            # Get the inserted record
            row = result.mappings().first()
            if row:
                result_dict = dict(row)
                # Convert ID to string if it exists
                if 'id' in result_dict and result_dict['id'] is not None:
                    result_dict['id'] = str(result_dict['id'])
                
                # Convert disabled to is_active for users table
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
        
        # Handle different collection types
        if collection == "notes":
            # Convert string ID to integer if it's a digit
            numeric_id = int(id) if isinstance(id, str) and id.isdigit() else id
            
            # Create a select statement using raw SQL
            sql = f"SELECT * FROM {collection} WHERE id = :id"
            
            # Execute the statement
            result = await self._session.execute(text(sql), {"id": numeric_id})
            
            # Get the record
            row = result.mappings().first()
            if row:
                result_dict = dict(row)
                # Convert ID to string if it exists
                if 'id' in result_dict and result_dict['id'] is not None:
                    result_dict['id'] = str(result_dict['id'])
                
                # Handle tags array if present
                if 'tags' in result_dict:
                    result_dict['tags'] = parse_postgres_array(result_dict['tags'], field_name='tags')
                    logger.info(f"Parsed tags in read method: {result_dict['tags']}")
                
                return result_dict
            return None
        elif collection == "users":
            # For users, we can search by ID or username
            if isinstance(id, str) and not id.isdigit():
                # Search by username
                sql = f"SELECT * FROM {collection} WHERE username = :username"
                result = await self._session.execute(text(sql), {"username": id})
            else:
                # Search by ID
                sql = f"SELECT * FROM {collection} WHERE id = :id"
                result = await self._session.execute(text(sql), {"id": id})
            
            # Get the record
            row = result.mappings().first()
            if row:
                result_dict = dict(row)
                # Convert ID to string if it exists
                if 'id' in result_dict and result_dict['id'] is not None:
                    result_dict['id'] = str(result_dict['id'])
                
                # Convert disabled to is_active
                if "disabled" in result_dict:
                    result_dict["is_active"] = not result_dict["disabled"]
                    del result_dict["disabled"]
                
                return result_dict
            return None
        else:
            # Standard handling for other collections
            # Create a select statement using raw SQL
            sql = f"SELECT * FROM {collection} WHERE id = :id"
            
            # Execute the statement
            result = await self._session.execute(text(sql), {"id": id})
            
            # Get the record
            row = result.mappings().first()
            if row:
                result_dict = dict(row)
                # Convert ID to string if it exists
                if 'id' in result_dict and result_dict['id'] is not None:
                    result_dict['id'] = str(result_dict['id'])
                
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
        
        # Handle different collection types
        if collection == "notes":
            # Convert string ID to integer if it's a digit
            numeric_id = int(id) if isinstance(id, str) and id.isdigit() else id
            
            # Create a copy of the data to avoid modifying the original
            update_data = data.copy()
            
            # Handle tags array if present
            if "tags" in data and isinstance(data["tags"], list):
                # No need to modify tags as PostgreSQL can handle arrays in parameters
                pass
            
            # Create an update statement using raw SQL
            set_clause = ", ".join(f"{key} = :{key}" for key in update_data.keys())
            sql = f"UPDATE {collection} SET {set_clause} WHERE id = :id RETURNING *"
            
            # Add ID to parameters
            params = {**update_data, "id": numeric_id}
            
            # Execute the statement
            result = await self._session.execute(text(sql), params)
            await self._session.commit()
            
            # Get the updated record
            row = result.mappings().first()
            if row:
                result_dict = dict(row)
                # Convert ID to string if it exists
                if 'id' in result_dict and result_dict['id'] is not None:
                    result_dict['id'] = str(result_dict['id'])
                
                # Handle tags array in the result
                if 'tags' in result_dict:
                    result_dict['tags'] = parse_postgres_array(result_dict['tags'], field_name='tags')
                    logger.info(f"Parsed tags in update method: {result_dict['tags']}")
                
                return result_dict
            return None
        else:
            # Standard handling for other collections
            # Create a copy of the data to avoid modifying the original
            update_data = data.copy()
            
            # Create an update statement using raw SQL
            set_clause = ", ".join(f"{key} = :{key}" for key in update_data.keys())
            sql = f"UPDATE {collection} SET {set_clause} WHERE id = :id RETURNING *"
            
            # Add ID to parameters
            params = {**update_data, "id": id}
            
            # Execute the statement
            result = await self._session.execute(text(sql), params)
            await self._session.commit()
            
            # Get the updated record
            row = result.mappings().first()
            if row:
                result_dict = dict(row)
                # Convert ID to string if it exists
                if 'id' in result_dict and result_dict['id'] is not None:
                    result_dict['id'] = str(result_dict['id'])
                
                # Convert disabled to is_active for users table
                if collection == "users" and "disabled" in result_dict:
                    result_dict["is_active"] = not result_dict["disabled"]
                    del result_dict["disabled"]
                
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
        
        # Handle different collection types
        if collection == "notes":
            # Convert string ID to integer if it's a digit
            numeric_id = int(id) if isinstance(id, str) and id.isdigit() else id
            
            # Create a delete statement using raw SQL
            sql = f"DELETE FROM {collection} WHERE id = :id"
            
            # Execute the statement
            result = await self._session.execute(text(sql), {"id": numeric_id})
            await self._session.commit()
            
            # Return True if a record was deleted
            return result.rowcount > 0
        else:
            # Standard handling for other collections
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
            tag_filter = None
            
            # First, extract tag filter if present to handle it specially
            if "tag" in query and collection == "notes":
                tag_filter = query.pop("tag")
                logger.info(f"Found tag filter: {tag_filter}")
            
            # Process regular filters
            for field, value in query.items():
                # Special handling for tags field
                if field == 'tags' and collection == 'notes':
                    # Use array containment operator for tags
                    where_clauses.append(f"tags @> ARRAY[:tags_value]::text[]")
                    params["tags_value"] = value
                    logger.info(f"Adding tags filter with value: {value}")
                else:
                    where_clauses.append(f"{field} = :{field}")
                    params[field] = value
            
            # Add tag filter with special syntax if it exists
            if tag_filter is not None:
                # Use text[] containment operator with string array
                where_clauses.append(f"tags @> ARRAY[:tag_value]::text[]")
                params["tag_value"] = tag_filter
                logger.info(f"Adding tag filter with value: {tag_filter}")
            
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
            
            # Handle tags array for notes
            if collection == "notes" and "tags" in record:
                record["tags"] = parse_postgres_array(record["tags"], field_name='tags')
                logger.info(f"Parsed tags in list method for record {record.get('id', 'unknown')}: {record['tags']}")
                
            records.append(record)
        return records


# Register the PostgreSQL adapter with the factory
DatabaseAdapterFactory.register("postgres", PostgresAdapter)
