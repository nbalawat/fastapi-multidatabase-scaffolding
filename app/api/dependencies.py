"""Dependencies for the API routes."""
from typing import Dict, Any

from fastapi import Depends

from app.core.security import get_current_user
from app.db.base import DatabaseAdapter, get_db_adapter as base_get_db_adapter

# Re-export the get_current_user function
get_current_user = get_current_user

# Re-export the get_db_adapter function
async def get_db_adapter() -> DatabaseAdapter:
    """Get the database adapter.
    
    This is a dependency that can be injected into API routes.
    
    Returns:
        The database adapter
    """
    return await base_get_db_adapter()
