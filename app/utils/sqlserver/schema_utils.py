from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from uuid import uuid4
import json

from app.utils.sqlserver.json_parser import parse_json_string

logger = logging.getLogger(__name__)

def prepare_sqlserver_model(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a model for storage in SQL Server.
    
    Args:
        data: The model data
        
    Returns:
        The prepared data
    """
    # Create a copy to avoid modifying the original
    db_model = data.copy()
    
    # Convert tags list to JSON string for SQL Server
    if "tags" in db_model:
        if db_model["tags"] is None:
            db_model["tags"] = "[]"
        else:
            db_model["tags"] = json.dumps(db_model["tags"])
        
    # Set timestamps
    if "created_at" not in db_model:
        db_model["created_at"] = datetime.now()
    
    # Generate ID if not present
    if "id" not in db_model:
        db_model["id"] = str(uuid4())
    
    # For SQL Server, we need to handle UUIDs specially
    # But we don't need to modify the UUID string itself
    # SQL Server adapter will handle the proper formatting during query execution
    
    return db_model

def convert_from_sqlserver_model(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a SQL Server model to an API model.
    
    Args:
        data: The database model data
        
    Returns:
        The API model data
    """
    # Create a copy to avoid modifying the original
    api_model = data.copy()
    
    # Handle SQL Server JSON string for tags
    if "tags" in api_model and isinstance(api_model["tags"], str):
        api_model["tags"] = parse_json_string(api_model["tags"], "tags")
        
    return api_model

def get_sqlserver_create_table_statement(table_name: str, columns: Dict[str, str]) -> str:
    """Generate a CREATE TABLE statement for SQL Server.
    
    Args:
        table_name: The table name
        columns: Dictionary of column names and their SQL Server types
        
    Returns:
        The CREATE TABLE statement
    """
    column_defs = []
    for column_name, column_type in columns.items():
        column_defs.append(f"    {column_name} {column_type}")
        
    # Join column definitions with proper newlines
    column_str = ',\n'.join(column_defs)
    
    return f"""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U')
    CREATE TABLE {table_name} (
{column_str}
    );
    """
