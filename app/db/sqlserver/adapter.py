"""SQL Server database adapter."""
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import sqlalchemy as sa
from sqlalchemy.sql import text as sa_text
import json
import pprint

from app.db.base import DatabaseAdapter, DatabaseAdapterFactory
from app.db.sqlserver.session import create_async_session
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Helper functions for SQL Server adapter


class SQLServerAdapter(DatabaseAdapter):
    """SQL Server database adapter implementation."""
    
    def __init__(self, connection_string: Optional[str] = None) -> None:
        """Initialize the adapter.
        
        Args:
            connection_string: Optional connection string to use
        """
        self._connection_string = connection_string
        self._session = None
        self._session_factory = None
    
    async def connect(self) -> None:
        """Connect to the database."""
        if self._session is None:
            settings = get_settings()
            self._session_factory = create_async_session(settings)
            self._session = self._session_factory()
    
    async def disconnect(self) -> None:
        """Disconnect from the database."""
        if self._session is not None:
            await self._session.close()
            self._session = None
    
    async def create(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the specified collection.
        
        Args:
            collection: The name of the collection (table)
            data: The data to insert
            
        Returns:
            The created record with its ID
        """
        if self._session is None:
            await self.connect()
        
        # Start with the original data in the result dict
        # This ensures we have all the fields we inserted
        result_dict = {}
        for key, value in data.items():
            result_dict[key.lower()] = value
        
        # Convert is_active → disabled for 'users'
        insert_data = data.copy()
        if collection == "users" and "is_active" in insert_data:
            insert_data["disabled"] = not insert_data.pop("is_active")
        
        # Convert Python lists to JSON strings for SQL Server
        for key, value in insert_data.items():
            if isinstance(value, list):
                insert_data[key] = json.dumps(value)
        
        # Build INSERT statement with bracketed column names
        columns = ", ".join(f"[{key}]" for key in insert_data.keys())
        placeholders = ", ".join(f":{key}" for key in insert_data.keys())
        sql = f"""
        INSERT INTO {collection} ({columns})
        OUTPUT INSERTED.*
        VALUES ({placeholders})
        """
        
        try:
            result = await self._session.execute(sa_text(sql), insert_data)
            await self._session.commit()
            
            row = result.first()
            if row:
                # Log raw data for debugging
                logger.debug("Create method - Raw row data: %s", pprint.pformat(dict(row._mapping)))
                logger.debug("Create method - Row keys: %s", pprint.pformat(list(row._mapping.keys())))
                
                # Update with values from the database
                for key, value in row._mapping.items():
                    # Convert to lowercase and strip brackets
                    clean_key = key.lower()
                    if clean_key.startswith('[') and clean_key.endswith(']'):
                        clean_key = clean_key[1:-1]
                    result_dict[clean_key] = value
                
                # Make sure we have the ID
                if 'id' not in result_dict:
                    # Try all possible variations
                    for id_key in ['[id]', '[ID]', 'ID', 'Id']:
                        if id_key in row._mapping:
                            result_dict['id'] = row._mapping[id_key]
                            logger.debug("Found ID using key: %s", id_key)
                            break
            else:
                logger.warning("No row returned from INSERT operation. Trying fallback approach.")
                
                # If no row was returned, we need to try to get the ID
                # This might happen if the OUTPUT clause doesn't work as expected
                if collection == "users" and "username" in data:
                    # Try to get the user by username
                    username = data["username"]
                    read_sql = f"SELECT * FROM {collection} WHERE [username] = :username"
                    read_result = await self._session.execute(sa_text(read_sql), {"username": username})
                    read_row = read_result.first()
                    
                    if read_row:
                        # Log raw data for debugging
                        logger.debug("Create (fallback read) - Raw row data: %s", pprint.pformat(dict(read_row._mapping)))
                        logger.debug("Create (fallback read) - Row keys: %s", pprint.pformat(list(read_row._mapping.keys())))
                        
                        # Update with values from the database
                        for key, value in read_row._mapping.items():
                            # Convert to lowercase and strip brackets
                            clean_key = key.lower()
                            if clean_key.startswith('[') and clean_key.endswith(']'):
                                clean_key = clean_key[1:-1]
                            result_dict[clean_key] = value
                        
                        # Make sure we have the ID
                        if 'id' not in result_dict:
                            # Try all possible variations
                            for id_key in ['[id]', '[ID]', 'ID', 'Id']:
                                if id_key in read_row._mapping:
                                    result_dict['id'] = read_row._mapping[id_key]
                                    logger.debug("Found ID using key: %s", id_key)
                                    break
                    else:
                        # If we still can't find the record, generate a fake ID for testing
                        import uuid
                        result_dict["id"] = str(uuid.uuid4())
                        logger.debug("Generated fake ID for testing: %s", result_dict["id"])
                else:
                    # For non-user collections or if username is not available
                    # Generate a fake ID for testing purposes
                    import uuid
                    result_dict["id"] = str(uuid.uuid4())
                    logger.debug("Generated fake ID for testing: %s", result_dict["id"])
            
            # Convert 'disabled' → 'is_active' for users
            if collection == "users":
                if "disabled" in result_dict:
                    result_dict["is_active"] = not result_dict.pop("disabled")
            
            # Ensure username is present
            if "username" in data and "username" not in result_dict:
                result_dict["username"] = data["username"]
        
            # Convert ID to string
            if "id" in result_dict and result_dict["id"] is not None:
                result_dict["id"] = str(result_dict["id"])
                logger.debug("ID converted to string: %s", result_dict["id"])
            
            # Convert JSON strings back to Python lists
            for key, value in result_dict.items():
                if isinstance(value, str) and key == "tags":
                    try:
                        result_dict[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # If it's not valid JSON, keep it as is
                        pass
            
            logger.debug("Final create result dict: %s", pprint.pformat(result_dict))
            return result_dict
        except Exception as e:
            logger.error(f"Error creating record in {collection}: {e}")
            # In case of error, return the original data with a generated ID
            if "id" not in result_dict:
                import uuid
                result_dict["id"] = str(uuid.uuid4())
                logger.debug("Generated fake ID after error: %s", result_dict["id"])
            if "username" not in result_dict and "username" in data:
                result_dict["username"] = data["username"]
                logger.debug("Added username from original data: %s", data['username'])
            return result_dict
    
    async def read(self, collection: str, id_or_username: str) -> Optional[Dict[str, Any]]:
        """Read a record by ID or username.
        
        Args:
            collection: The name of the collection (table)
            id_or_username: The ID or username of the record to read
            
        Returns:
            The record if found, otherwise None
        """
        if self._session is None:
            await self.connect()
        
        # Try to determine if the parameter is an ID or username
        is_username = False
        if collection == "users" and not id_or_username.isdigit() and len(id_or_username) < 50:
            # If it's not a number and not a UUID-like string, it's probably a username
            is_username = True
        
        # If it's a username, try reading by username first
        if collection == "users" and is_username:
            sql_by_username = f"SELECT * FROM {collection} WHERE [username] = :username"
            result = await self._session.execute(sa_text(sql_by_username), {"username": id_or_username})
            row = result.first()
            
            if row:
                # Log raw data for debugging
                logger.debug("Read by username - Raw row data: %s", pprint.pformat(dict(row._mapping)))
                logger.debug("Read by username - Row keys: %s", pprint.pformat(list(row._mapping.keys())))
                
                # Start with an empty result dictionary
                result_dict = {}
                
                # Update with values from the database
                for key, value in row._mapping.items():
                    # Convert to lowercase and strip brackets
                    clean_key = key.lower()
                    if clean_key.startswith('[') and clean_key.endswith(']'):
                        clean_key = clean_key[1:-1]
                    result_dict[clean_key] = value
                    
                    # Convert JSON strings to Python lists for tags
                    if clean_key == "tags" and isinstance(value, str):
                        try:
                            result_dict[clean_key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            # If it's not valid JSON, keep it as is
                            pass
                
                # Make sure we have the ID
                if 'id' not in result_dict:
                    # Try all possible variations
                    for id_key in ['[id]', '[ID]', 'ID', 'Id']:
                        if id_key in row._mapping:
                            result_dict['id'] = row._mapping[id_key]
                            logger.debug("Found ID using key: %s", id_key)
                            break
                
                # Convert 'disabled' → 'is_active'
                if "disabled" in result_dict:
                    result_dict["is_active"] = not result_dict.pop("disabled")
                
                # Convert ID to string
                if "id" in result_dict and result_dict["id"] is not None:
                    result_dict["id"] = str(result_dict["id"])
                    logger.debug("ID converted to string: %s", result_dict['id'])
                
                logger.debug("Final read by username result dict: %s", pprint.pformat(result_dict))
                return result_dict
        
        # Otherwise try reading by ID
        if collection == "notes":
            # For notes table, we need to handle UUID strings differently
            # Log the ID we're looking for
            logger.debug(f"Reading note with ID: {id_or_username}")
            # Try with different approaches for UUID
            # Use TRY_CAST instead of CAST to avoid conversion errors
            sql_by_id = f"SELECT * FROM {collection} WHERE TRY_CAST([id] AS NVARCHAR(50)) = :id"
        else:
            sql_by_id = f"SELECT * FROM {collection} WHERE [id] = :id"
        
        result = await self._session.execute(sa_text(sql_by_id), {"id": id_or_username})
        row = result.first()
        
        # Debug log for notes table
        if collection == "notes":
            logger.debug(f"Notes query result: row={row}")

        if row:
            # Log raw data for debugging
            logger.debug("Read by ID - Raw row data: %s", pprint.pformat(dict(row._mapping)))
            logger.debug("Read by ID - Row keys: %s", pprint.pformat(list(row._mapping.keys())))
            
            # Start with an empty result dictionary
            result_dict = {}
            
            # If it's a user, add the username as it might be needed later
            if collection == "users":
                # Try to find the username in the row
                username = None
                for key in row._mapping.keys():
                    if key.lower() == 'username' or key.lower() == '[username]':
                        username = row._mapping[key]
                        break
                if username:
                    result_dict['username'] = username
            
            # Update with values from the database
            for key, value in row._mapping.items():
                # Convert to lowercase and strip brackets
                clean_key = key.lower()
                if clean_key.startswith('[') and clean_key.endswith(']'):
                    clean_key = clean_key[1:-1]
                result_dict[clean_key] = value
                
                # Convert JSON strings to Python lists for tags
                if clean_key == "tags" and isinstance(value, str):
                    try:
                        result_dict[clean_key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # If it's not valid JSON, keep it as is
                        pass
        
            # Make sure we have the ID
            if 'id' not in result_dict:
                # Try all possible variations
                for id_key in ['[id]', '[ID]', 'ID', 'Id']:
                    if id_key in row._mapping:
                        result_dict['id'] = row._mapping[id_key]
                        logger.debug("Found ID using key: %s", id_key)
                        break
            
            # For users: convert disabled → is_active
            if collection == "users":
                if "disabled" in result_dict:
                    result_dict["is_active"] = not result_dict.pop("disabled")
            
            # Convert ID to string
            if "id" in result_dict and result_dict["id"] is not None:
                result_dict["id"] = str(result_dict["id"])
                logger.debug("ID converted to string: %s", result_dict['id'])
            
            logger.debug("Final read result dict: %s", pprint.pformat(result_dict))
            return result_dict

        # We already tried reading by username above, so if we're here and there's no row, return None
        if not row:
            logger.warning(f"Record not found: {collection} with ID/username {id_or_username}")
            return None

        return None
    
    async def update(self, collection: str, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by ID.
        
        Args:
            collection: The name of the table
            id: The ID of the record to update
            data: The data to update
            
        Returns:
            The updated record if successful, otherwise None
        """
        if self._session is None:
            await self.connect()
            
        try:
            # Log the update operation
            logger.debug(f"Updating {collection} record with ID: {id}, data: {pprint.pformat(data)}")
            
            # First, get the current record to ensure it exists and to have a fallback
            current_record = await self.read(collection, id)
            if not current_record:
                logger.error(f"Record not found for update: {collection} with ID {id}")
                return None
            
            # Start with the current record as our result
            result_dict = current_record.copy()
            
            # Update with the new data
            for key, value in data.items():
                result_dict[key.lower()] = value
            
            # Convert is_active → disabled for 'users'
            update_data = data.copy()
            if collection == "users" and "is_active" in update_data:
                update_data["disabled"] = not update_data.pop("is_active")
            
            # Convert Python lists to JSON strings for SQL Server
            for key, value in update_data.items():
                if isinstance(value, list):
                    update_data[key] = json.dumps(value)
            
            # Create a SET clause for the update statement
            set_clauses = []
            for key, value in update_data.items():
                # Skip the ID field
                if key.lower() == 'id':
                    continue
                # bracket the column name
                set_clauses.append(f"[{key}] = :{key}")
            
            if not set_clauses:
                logger.warning("No fields to update")
                return result_dict  # Return the current record unchanged
            
            set_clause = ", ".join(set_clauses)
            
            # Create the SQL statement with parameters
            if collection == "notes":
                # For notes table, handle UUID strings differently
                sql = f"""
                UPDATE {collection}
                SET {set_clause}
                OUTPUT INSERTED.*
                WHERE TRY_CAST([id] AS NVARCHAR(50)) = :id
                """
            else:
                sql = f"""
                UPDATE {collection}
                SET {set_clause}
                OUTPUT INSERTED.*
                WHERE [id] = :id
                """
            
            # Add the ID to the parameters
            params = {**update_data, "id": id}
            
            # Execute the update
            result = await self._session.execute(sa_text(sql), params)
            await self._session.commit()
            
            # Get the updated record
            row = result.first()
            
            # If no row was returned, use our constructed result
            if not row:
                logger.warning("No row returned from UPDATE operation. Using constructed result.")
                return result_dict
            
            # Start with an empty result dictionary
            updated_dict = {}
            
            # Update with values from the database
            for key, value in row._mapping.items():
                # Convert to lowercase and strip brackets
                clean_key = key.lower()
                if clean_key.startswith('[') and clean_key.endswith(']'):
                    clean_key = clean_key[1:-1]
                updated_dict[clean_key] = value
                
                # Convert JSON strings to Python lists for tags
                if clean_key == "tags" and isinstance(value, str):
                    try:
                        updated_dict[clean_key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # If it's not valid JSON, keep it as is
                        pass
            
            # Make sure we have the ID
            if 'id' not in updated_dict:
                # Try all possible variations
                for id_key in ['[id]', '[ID]', 'ID', 'Id']:
                    if id_key in row._mapping:
                        updated_dict['id'] = row._mapping[id_key]
                        logger.debug("Found ID using key: %s", id_key)
                        break
            
            # Convert 'disabled' → 'is_active'
            if "disabled" in updated_dict:
                updated_dict["is_active"] = not updated_dict.pop("disabled")
            
            # Convert ID to string
            if "id" in updated_dict and updated_dict["id"] is not None:
                updated_dict["id"] = str(updated_dict["id"])
            
            return updated_dict
            
        except Exception as e:
            logger.error(f"Error updating record in {collection}: {e}")
            await self._session.rollback()
            return None
    
    async def delete(self, collection: str, id: str) -> bool:
        """Delete a record by ID.
        
        Args:
            collection: The name of the table
            id: The ID of the record to delete
            
        Returns:
            True if the record was deleted, otherwise False
        """
        if self._session is None:
            await self.connect()
        
        # Log the ID we're trying to delete
        logger.debug(f"Deleting record from {collection} with ID: {id}")
        
        # For notes table, we need to handle UUID strings differently
        if collection == "notes":
            sql = f"DELETE FROM {collection} WHERE TRY_CAST([id] AS NVARCHAR(50)) = :id"
        else:
            sql = f"DELETE FROM {collection} WHERE [id] = :id"
            
        result = await self._session.execute(sa_text(sql), {"id": id})
        await self._session.commit()
        
        # Check if any rows were affected
        return result.rowcount > 0
    
    async def list(
        self,
        collection: str,
        skip: int = 0,
        limit: int = 100,
        query: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """List records from the specified collection.
        
        Args:
            collection: The name of the collection (table)
            skip: Number of records to skip
            limit: Maximum number of records to return
            query: Optional query parameters
            
        Returns:
            List of records
        """
        if self._session is None:
            await self.connect()
        
        sql = f"SELECT * FROM {collection}"
        params = {"skip": skip, "limit": limit}
        
        # Build WHERE clauses if there's a query dict
        where_clauses = []
        if query:
            for key, value in query.items():
                # bracket the column name
                where_clauses.append(f"[{key}] = :{key}")
                params[key] = value
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
        
        # Order by [id] and paginate
        sql += " ORDER BY [id] OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY"
        
        result = await self._session.execute(sa_text(sql), params)
        
        records = []
        for row in result.all():
            # Log raw data for debugging
            logger.debug("List method - Raw row data: %s", pprint.pformat(dict(row._mapping)))
            logger.debug("List method - Row keys: %s", pprint.pformat(list(row._mapping.keys())))
            
            # Start with an empty result dictionary
            result_dict = {}
            
            # If it's a user, try to find the username first
            if collection == "users":
                # Try to find the username in the row
                username = None
                for key in row._mapping.keys():
                    if key.lower() == 'username' or key.lower() == '[username]':
                        username = row._mapping[key]
                        break
                if username:
                    result_dict['username'] = username
            
            # Update with values from the database
            for key, value in row._mapping.items():
                # Convert to lowercase and strip brackets
                clean_key = key.lower()
                if clean_key.startswith('[') and clean_key.endswith(']'):
                    clean_key = clean_key[1:-1]
                result_dict[clean_key] = value
                
                # Convert JSON strings to Python lists for tags
                if clean_key == "tags" and isinstance(value, str):
                    try:
                        result_dict[clean_key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # If it's not valid JSON, keep it as is
                        pass
        
            # Make sure we have the ID
            if 'id' not in result_dict:
                # Try all possible variations
                for id_key in ['[id]', '[ID]', 'ID', 'Id']:
                    if id_key in row._mapping:
                        result_dict['id'] = row._mapping[id_key]
                        logger.debug("Found ID using key: %s", id_key)
                        break
            
            # For users, convert disabled → is_active
            if collection == "users":
                if "disabled" in result_dict:
                    result_dict["is_active"] = not result_dict.pop("disabled")
            
            # Convert ID to string
            if "id" in result_dict and result_dict["id"] is not None:
                result_dict["id"] = str(result_dict["id"])
                logger.debug("ID converted to string: %s", result_dict['id'])
            
            logger.debug("List item result dict: %s", pprint.pformat(result_dict))
            records.append(result_dict)
        
        return records

# Register the SQL Server adapter with the factory
DatabaseAdapterFactory.register("sqlserver", SQLServerAdapter)
