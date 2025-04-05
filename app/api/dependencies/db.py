"""Database dependencies for FastAPI."""
from typing import AsyncGenerator

from app.db.base import DatabaseAdapter, DatabaseAdapterFactory
from app.core.config import get_settings

async def get_db_adapter() -> AsyncGenerator[DatabaseAdapter, None]:
    """Get the database adapter.
    
    This is a dependency that can be injected into API routes.
    Handles connecting and disconnecting from the database automatically.
    
    Yields:
        The database adapter
    """
    settings = get_settings()
    adapter = DatabaseAdapterFactory.get_adapter(settings.db_type)
    await adapter.connect()
    try:
        yield adapter
    finally:
        await adapter.disconnect()
