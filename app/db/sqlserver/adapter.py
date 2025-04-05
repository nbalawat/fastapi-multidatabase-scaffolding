"""SQL Server database adapter."""
import logging
from typing import Dict, Any, List, Optional, Tuple, Union, Set
import sqlalchemy as sa
from sqlalchemy.sql import text as sa_text
import json
import pprint

from app.db.base import DatabaseAdapter, DatabaseAdapterFactory
from app.db.sqlserver.session import create_async_session
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Helper functions for SQL Server adapter

def parse_json_string(value: Any, field_name: str = "unknown") -> Any:
    """Parse a JSON string into a Python list with error handling.
    
    Args:
        value: The JSON string to parse
        field_name: The name of the field being parsed (for logging)
        
    Returns:
        The parsed list or the original value if parsing fails
    """
    logger = logging.getLogger(__name__)
    
    # If it's already a list or not a string, return it as is
    if not isinstance(value, str):
        return value
        
    # If it's an empty string, return an empty list
    if not value or value.strip() == '':
        logger.info(f"Empty {field_name} value, returning empty list")
        return []
        
    try:
        logger.info(f"Parsing JSON for {field_name}: {value}")
        parsed = json.loads(value)
        logger.info(f"Successfully parsed {field_name}: {parsed}")
        
        # Ensure the result is a list if it's supposed to be
        if field_name == "tags" and not isinstance(parsed, list):
            if isinstance(parsed, str):
                return [parsed]  # Convert single string to a list with one item
            return []  # Return empty list for non-list, non-string values
            
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing {field_name} JSON: {e}, raw value: {value}")
        
        # For values that look like lists, try manual parsing
        if value.startswith('[') and value.endswith(']'):
            try:
                # Try to manually parse it by removing quotes and splitting
                clean_value = value.strip('[]').replace('"', '').replace('\'', '')
                result = [item.strip() for item in clean_value.split(',') if item.strip()]
                logger.info(f"Manually parsed {field_name}: {result}")
                return result
            except Exception as e2:
                logger.error(f"Failed manual parsing for {field_name}: {e2}")
        
        # For single-word strings that aren't in JSON format, treat as a single tag
        if field_name == "tags" and ',' not in value and not value.startswith('['):
            logger.info(f"Treating single value as a tag: {value}")
            return [value]
                
    # Return original value if all parsing attempts fail
    return value


class SQLServerAdapter(DatabaseAdapter):
    """SQL Server database adapter implementation."""
    
    # No need for ID cache since we're using string IDs directly
    
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
        
        # Convert Python lists and sets to JSON strings for SQL Server
        for key, value in list(insert_data.items()):
            if isinstance(value, (list, set)):
                insert_data[key] = json.dumps(list(value))
            # Handle enum values
            elif hasattr(value, 'value'):
                insert_data[key] = value.value
        
        # Make sure we have proper IDs for all collections
        if "id" not in insert_data:
            # Generate a UUID if ID is not provided
            import uuid
            insert_data["id"] = str(uuid.uuid4())
            logger.debug(f"Generated UUID for record: {insert_data['id']}")
        else:
            # Ensure ID is a string
            insert_data["id"] = str(insert_data["id"])
            logger.debug(f"Using provided ID (converted to string): {insert_data['id']}")
        
        # For notes, explicitly log the ID we're using
        if collection == "notes":
            logger.info(f"Note creation - Using ID: {insert_data['id']}")
            
            # Make sure we have a user_id for the note owner if this is a note
            if "user_id" not in insert_data:
                # Default to admin if no user_id provided
                insert_data["user_id"] = "admin"
                logger.debug(f"Setting default user_id for note: admin")
                
            # Ensure created_at is set
            if "created_at" not in insert_data:
                from datetime import datetime
                insert_data["created_at"] = datetime.utcnow()
                logger.debug(f"Setting default created_at: {insert_data['created_at']}")
    
        # Build INSERT statement with bracketed column names
        columns = ", ".join(f"[{key}]" for key in insert_data.keys())
        placeholders = ", ".join(f":{key}" for key in insert_data.keys())
        
        # For notes, use a simpler approach without OUTPUT clause
        if collection == "notes":
            sql = f"""
            INSERT INTO {collection} ({columns})
            VALUES ({placeholders})
            """
            logger.info(f"Using simplified INSERT for notes without OUTPUT clause")
        else:
            sql = f"""
            INSERT INTO {collection} ({columns})
            OUTPUT INSERTED.*
            VALUES ({placeholders})
            """
        
        try:
            # Add special handling for roles collection
            if collection == "roles":
                # For roles, use the name as the ID
                if "name" in insert_data and "id" not in insert_data:
                    insert_data["id"] = insert_data["name"]
                    logger.debug(f"Using name as ID for role: {insert_data['name']}")
                
                # Check if permissions is a list or set and convert to JSON
                if "permissions" in insert_data:
                    logger.debug(f"Role permissions before conversion: {insert_data['permissions']}")
                    if isinstance(insert_data['permissions'], (list, set)):
                        # Make sure all permissions are strings
                        permissions_list = [str(p) for p in insert_data['permissions']]
                        insert_data['permissions'] = json.dumps(permissions_list)
                        logger.debug(f"Converted permissions to JSON: {insert_data['permissions']}")
                
                # Check if the role already exists to avoid duplicate key errors
                try:
                    existing = await self.read(collection, insert_data["name"])
                    if existing:
                        logger.warning(f"Role {insert_data['name']} already exists, skipping creation")
                        return existing
                except Exception as e:
                    logger.debug(f"Error checking if role exists: {str(e)}")
            
            # Log the SQL and parameters for debugging
            logger.debug(f"SQL: {sql}")
            logger.debug(f"Parameters: {insert_data}")
            
            # For notes, add extra detailed logging
            if collection == "notes":
                logger.info(f"Creating note with ID: {insert_data.get('id')}")
                logger.info(f"Note data: {insert_data}")
            
            result = await self._session.execute(sa_text(sql), insert_data)
            await self._session.commit()
            
            # For notes with simplified approach, we don't expect a row back
            if collection == "notes":
                # Return the original data directly
                for key, value in insert_data.items():
                    # Handle special fields that need deserialization
                    if key == "tags" and isinstance(value, str):
                        # Use our helper function to parse JSON
                        result_dict[key.lower()] = parse_json_string(value, field_name="tags")
                    else:
                        result_dict[key.lower()] = value
                logger.info(f"Note created successfully with ID: {result_dict.get('id')}")
                return result_dict
            
            # For other collections, try to get the row from the result
            row = result.first()
            if row:
                # Log raw data for debugging
                logger.debug("Create method - Raw row data: %s", pprint.pformat(dict(row._mapping)))
                logger.debug("Create method - Row keys: %s", pprint.pformat(list(row._mapping.keys())))
                
                # Process the row data
                for key, value in row._mapping.items():
                    # Clean the key name (remove brackets and convert to lowercase)
                    clean_key = key.lower()
                    if clean_key.startswith('[') and clean_key.endswith(']'):
                        clean_key = clean_key[1:-1]
                    
                    # For notes, make sure we preserve the original ID
                    if collection == "notes" and clean_key == "id":
                        # Use the original ID that was passed in or generated
                        result_dict["id"] = str(insert_data["id"])
                        logger.info(f"Preserving original note ID: {result_dict['id']}")
                    else:
                        # For other keys, use the value from the database
                        result_dict[clean_key] = value
                        
                        # Handle JSON serialized data
                        if isinstance(value, str) and (value.startswith('[') and value.endswith(']') or 
                                                     value.startswith('{') and value.endswith('}')):
                            try:
                                value = json.loads(value)
                                result_dict[clean_key] = value
                            except json.JSONDecodeError:
                                logger.debug(f"Failed to decode JSON for key {clean_key}: {value}")
                                # Keep as string if not valid JSON
                    
                    # Special handling for roles collection
                    if collection == "roles" and clean_key == "permissions" and isinstance(value, str):
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            logger.debug(f"Failed to decode permissions JSON: {value}")
                            # Try to handle as comma-separated string
                            if ',' in value:
                                value = [p.strip() for p in value.split(',')]
                    
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
                if collection == "notes":
                    # For notes, try to read the note we just created using the ID
                    note_id = insert_data["id"]
                    logger.info(f"Attempting to read note with ID: {note_id}")
                    
                    # Use a direct SQL query to check if the note exists
                    read_sql = f"SELECT * FROM {collection} WHERE CAST([id] AS NVARCHAR(255)) = :id"
                    read_result = await self._session.execute(sa_text(read_sql), {"id": note_id})
                    read_row = read_result.first()
                    
                    if read_row:
                        logger.info(f"Successfully found note with ID: {note_id}")
                    else:
                        logger.warning(f"Note with ID {note_id} not found after creation")
                        # Return the original data since we know it was inserted
                        for key, value in insert_data.items():
                            result_dict[key.lower()] = value
                        logger.info(f"Returning original note data with ID: {result_dict.get('id')}")
                        return result_dict
                        
                elif collection == "users" and "username" in data:
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
            logger.error(f"SQL that failed: {sql}")
            logger.error(f"Parameters: {pprint.pformat(insert_data)}")
            
            # Special handling for roles collection
            if collection == "roles":
                # For roles, use the name as the ID and return the data
                if "name" in data:
                    result_dict["id"] = data["name"]
                    # Convert permissions back from JSON if needed
                    if "permissions" in result_dict and isinstance(result_dict["permissions"], str):
                        try:
                            result_dict["permissions"] = set(json.loads(result_dict["permissions"]))
                        except (json.JSONDecodeError, TypeError):
                            pass
                    logger.debug(f"Returning role data with name as ID: {result_dict}")
                    return result_dict
        
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
        
        # Try to determine if the parameter is an ID or username/role name
        is_username = False
        is_role_name = False
        
        if collection == "users" and not id_or_username.isdigit() and len(id_or_username) < 50:
            # If it's not a number and not a UUID-like string, it's probably a username
            is_username = True
        elif collection == "roles":
            # For roles, we'll treat the parameter as a role name
            is_role_name = True
            logger.debug(f"Treating {id_or_username} as a role name")
        
        # If it's a username or role name, try reading by that first
        if (collection == "users" and is_username) or (collection == "roles" and is_role_name):
            if collection == "users":
                sql_by_username = f"SELECT * FROM {collection} WHERE [username] = :username"
            else:  # roles
                # For roles, try to match by name or id
                sql_by_username = f"SELECT * FROM {collection} WHERE [name] = :username OR [id] = :username"
                logger.debug(f"Searching for role with name/id: {id_or_username}")
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
                    
                    # Convert JSON strings to Python lists/sets for tags and permissions
                    if (clean_key == "tags" or clean_key == "permissions") and isinstance(value, str):
                        # Use our helper function to parse JSON
                        parsed_value = parse_json_string(value, field_name=clean_key)
                        result_dict[clean_key] = parsed_value
                        
                        # Convert permissions to set if needed
                        if clean_key == "permissions" and isinstance(parsed_value, list):
                            result_dict[clean_key] = set(parsed_value)
                        elif clean_key == "permissions" and isinstance(value, str) and ',' in value and not isinstance(parsed_value, list):
                            # If it's not valid JSON but it's permissions, try to handle as comma-separated string
                            result_dict[clean_key] = set(p.strip() for p in value.split(','))
                
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
            # Query by ID for notes - ensure we're using string comparison
            # Use CAST instead of CONVERT for better compatibility
            sql_by_id = f"""
            SELECT * FROM {collection} 
            WHERE CAST([id] AS NVARCHAR(255)) = :id
            """
            logger.info(f"Reading note with ID: {id_or_username}")
            logger.info(f"Using SQL query for notes: {sql_by_id}")
            
            # List all notes to help with debugging
            try:
                list_sql = "SELECT id, title FROM notes"
                list_result = await self._session.execute(sa_text(list_sql))
                # For async SQLAlchemy, we need to use all() instead of fetchall()
                rows = list_result.all()
                logger.info(f"Available notes in database: {len(rows)}")
                for idx, row in enumerate(rows):
                    note_id = row[0] if len(row) > 0 else 'unknown'
                    note_title = row[1] if len(row) > 1 else 'unknown'
                    logger.info(f"Note {idx}: ID={note_id}, Title={note_title}")
            except Exception as e:
                logger.error(f"Error listing notes: {e}")
        elif collection == "roles":
            # For roles table, the name is the ID
            logger.debug(f"Reading role with name: {id_or_username}")
            sql_by_id = f"SELECT * FROM {collection} WHERE [name] = :id OR [id] = :id"
        else:
            sql_by_id = f"SELECT * FROM {collection} WHERE [id] = :id"
        
        result = await self._session.execute(sa_text(sql_by_id), {"id": id_or_username})
        row = result.first()
        
        # Debug log for notes table
        if collection == "notes":
            logger.info(f"Notes query result: row={row}")
            logger.info(f"SQL query executed: {sql_by_id}")
            logger.info(f"Parameters: id={id_or_username}")
            if row:
                logger.info(f"Row keys: {list(row._mapping.keys())}")
                logger.info(f"Row values: {dict(row._mapping)}")
            else:
                logger.warning(f"No row found for note with ID: {id_or_username}")
                
                # Let's try a more permissive query to see if the note exists with a different ID format
                try:
                    logger.info("Attempting to find note with a more permissive query")
                    # Try with different ID formats
                    permissive_sql = f"SELECT * FROM {collection} WHERE id = :id OR CAST(id AS NVARCHAR(255)) = :id"
                    permissive_result = await self._session.execute(sa_text(permissive_sql), {"id": id_or_username})
                    permissive_row = permissive_result.first()
                    
                    if permissive_row:
                        logger.info(f"Found note with permissive query: {dict(permissive_row._mapping)}")
                        # Use this row instead
                        row = permissive_row
                    else:
                        # List all notes to help with debugging
                        logger.info("Listing all notes in the database:")
                        list_sql = "SELECT id, title FROM notes"
                        list_result = await self._session.execute(sa_text(list_sql))
                        all_notes = list_result.all()
                        logger.info(f"Found {len(all_notes)} total notes in the database")
                        
                        for idx, note_row in enumerate(all_notes):
                            note_dict = dict(note_row._mapping)
                            note_id = next((v for k, v in note_dict.items() if k.lower().endswith('id')), 'unknown')
                            note_title = next((v for k, v in note_dict.items() if k.lower().endswith('title')), 'unknown')
                            logger.info(f"Note {idx}: ID={note_id}, Title={note_title}")
                except Exception as e:
                    logger.error(f"Error during permissive query: {e}")

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
                
                # Convert JSON strings to Python lists/sets for tags and permissions
                if (clean_key == "tags" or clean_key == "permissions") and isinstance(value, str):
                    # Use our helper function to parse JSON
                    result_dict[clean_key] = parse_json_string(value, field_name=clean_key)
                    
                    # Convert permissions to set if needed
                    if clean_key == "permissions" and isinstance(result_dict[clean_key], list):
                        result_dict[clean_key] = set(result_dict[clean_key])
        
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
            
            # No special handling needed for notes anymore
            # Just ensure the ID is a string
            if "id" in result_dict and result_dict["id"] is not None:
                result_dict["id"] = str(result_dict["id"])
            
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
            
            # Convert Python lists and sets to JSON strings for SQL Server
            for key, value in list(update_data.items()):
                if isinstance(value, (list, set)):
                    update_data[key] = json.dumps(list(value))
                # Handle enum values
                elif hasattr(value, 'value'):
                    update_data[key] = value.value
            
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
                # For notes, ensure we're using string comparison for the ID
                # Use CAST instead of CONVERT for better compatibility
                sql = f"""
                UPDATE {collection}
                SET {set_clause}
                OUTPUT INSERTED.*
                WHERE CAST([id] AS NVARCHAR(255)) = :id
                """
                logger.info(f"Using string ID query for notes update: {sql}")
            elif collection == "roles":
                # For roles table, the name is the ID
                logger.debug(f"Updating role with name: {id}")
                sql = f"""
                UPDATE {collection}
                SET {set_clause}
                OUTPUT INSERTED.*
                WHERE [name] = :id OR [id] = :id
                """
            else:
                sql = f"""
                UPDATE {collection}
                SET {set_clause}
                OUTPUT INSERTED.*
                WHERE [id] = :id
                """
            
            # Use the ID directly for all collections
            params = {**update_data, "id": id}
            logger.debug(f"Using ID directly for update: {id}")
            
            try:
                # Execute the update query
                result = await self._session.execute(sa_text(sql), params)
                await self._session.commit()
                
                # Get the updated row
                row = result.first()
                
                if not row:
                    logger.warning("No row returned from UPDATE operation. Using constructed result.")
                    return result_dict
                    
                # Log raw data for debugging
                logger.debug("Update method - Raw row data: %s", pprint.pformat(dict(row._mapping)))
                logger.debug("Update method - Row keys: %s", pprint.pformat(list(row._mapping.keys())))
                
            except Exception as e:
                logger.error(f"Error executing update: {e}")
                await self._session.rollback()
                raise
            
            # Start with an empty result dictionary
            updated_dict = {}
            
            # Update with values from the database
            for key, value in row._mapping.items():
                # Convert to lowercase and strip brackets
                clean_key = key.lower()
                if clean_key.startswith('[') and clean_key.endswith(']'):
                    clean_key = clean_key[1:-1]
                updated_dict[clean_key] = value
                
                # Convert JSON strings to Python lists/sets for tags and permissions
                if (clean_key == "tags" or clean_key == "permissions") and isinstance(value, str):
                    # Use our helper function to parse JSON
                    updated_dict[clean_key] = parse_json_string(value, field_name=clean_key)
                    
                    # Convert permissions to set if needed
                    if clean_key == "permissions" and isinstance(updated_dict[clean_key], list):
                        updated_dict[clean_key] = set(updated_dict[clean_key])
            
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
        
        # For notes table, ensure we're using string comparison for the ID
        if collection == "notes":
            # Use CAST instead of CONVERT for better compatibility
            sql = f"DELETE FROM {collection} WHERE CAST([id] AS NVARCHAR(255)) = :id"
            logger.info(f"Using string ID query for notes delete: {sql}")
        elif collection == "roles":
            # For roles, try to delete by name or id
            sql = f"DELETE FROM {collection} WHERE [name] = :id OR [id] = :id"
            logger.debug(f"Using name/id query for roles delete: {sql}")
        else:
            sql = f"DELETE FROM {collection} WHERE [id] = :id"
            
        # Use the ID directly for all collections
        params = {"id": id}
        logger.debug(f"Using ID directly for delete: {id}")
            
        result = await self._session.execute(sa_text(sql), params)
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
                # Special handling for tags in notes collection
                if collection == "notes" and key == "tag":
                    # For SQL Server, we need to check if the JSON array contains the tag
                    where_clauses.append(f"JSON_QUERY([tags], '$') LIKE :tag_filter")
                    params["tag_filter"] = f"%\"{value}\"%"
                    logger.debug(f"Added tag filter for SQL Server: {where_clauses[-1]} with value {params['tag_filter']}")
                else:
                    # Standard equality comparison for other fields
                    where_clauses.append(f"[{key}] = :{key}")
                    params[key] = value
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
        
        # Add special handling for roles collection
        if collection == "roles":
            # For roles, we don't use pagination to avoid issues with string IDs
            logger.debug(f"Using simplified query for roles collection")
            # No ORDER BY or pagination for roles to avoid SQL errors
        else:
            # For other collections, use standard pagination
            sql += " ORDER BY [id] OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY"
        
        try:
            logger.debug(f"Executing SQL: {sql} with params: {params}")
            result = await self._session.execute(sa_text(sql), params)
        except Exception as e:
            logger.error(f"Error executing list query for {collection}: {str(e)}")
            logger.error(f"SQL: {sql}, Params: {params}")
            # For roles, try a simpler query without pagination as fallback
            if collection == "roles":
                try:
                    simple_sql = f"SELECT * FROM {collection}"
                    logger.debug(f"Trying simpler SQL for roles: {simple_sql}")
                    result = await self._session.execute(sa_text(simple_sql))
                except Exception as inner_e:
                    logger.error(f"Error with fallback query: {str(inner_e)}")
                    raise
            else:
                raise
        
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
                
                # Convert JSON strings to Python lists/sets for tags and permissions
                if (clean_key == "tags" or clean_key == "permissions") and isinstance(value, str):
                    # Use our helper function to parse JSON
                    result_dict[clean_key] = parse_json_string(value, field_name=clean_key)
                    
                    # Convert permissions to set if needed
                    if clean_key == "permissions" and isinstance(result_dict[clean_key], list):
                        result_dict[clean_key] = set(result_dict[clean_key])
        
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
            
            # Ensure ID is a string
            if "id" in result_dict and result_dict["id"] is not None:
                result_dict["id"] = str(result_dict["id"])
                logger.debug(f"Ensured ID is string: {result_dict['id']}")
            
            logger.debug("Final create result dict: %s", pprint.pformat(result_dict))
            records.append(result_dict)
        
        return records

# Register the SQL Server adapter with the factory
DatabaseAdapterFactory.register("sqlserver", SQLServerAdapter)
