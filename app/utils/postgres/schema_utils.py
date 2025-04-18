from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from uuid import uuid4

from app.utils.postgres.array_parser import parse_postgres_array

logger = logging.getLogger(__name__)

def prepare_postgres_model(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a model for storage in PostgreSQL.
    
    Args:
        data: The model data
        
    Returns:
        The prepared data
    """
    # Create a copy to avoid modifying the original
    db_model = data.copy()
    
    # Ensure tags is a list for PostgreSQL array
    if "tags" in db_model and db_model["tags"] is None:
        db_model["tags"] = []
        
    # Set timestamps
    if "created_at" not in db_model:
        db_model["created_at"] = datetime.now()
    
    # Generate ID if not present
    if "id" not in db_model:
        db_model["id"] = str(uuid4())
        
    return db_model

def convert_from_postgres_model(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a PostgreSQL model to an API model.
    
    Args:
        data: The database model data
        
    Returns:
        The API model data
    """
    # Create a copy to avoid modifying the original
    api_model = data.copy()
    
    # Handle PostgreSQL array format for tags
    if "tags" in api_model and isinstance(api_model["tags"], str):
        api_model["tags"] = parse_postgres_array(api_model["tags"], "tags")
    
    # Ensure UUID objects are converted to strings
    if "id" in api_model and not isinstance(api_model["id"], str):
        api_model["id"] = str(api_model["id"])
        
    return api_model

def get_postgres_create_table_statement(table_name: str, columns: Dict[str, str]) -> str:
    """Generate a CREATE TABLE statement for PostgreSQL.
    
    Args:
        table_name: The table name
        columns: Dictionary of column names and their PostgreSQL types
        
    Returns:
        The CREATE TABLE statement
    """
    column_defs = []
    for column_name, column_type in columns.items():
        column_defs.append(f"    {column_name} {column_type}")
        
    # Join column definitions with proper newlines
    column_str = ',\n'.join(column_defs)
    
    return f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
{column_str}
    );
    """
