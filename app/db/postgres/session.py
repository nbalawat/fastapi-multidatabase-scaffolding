from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings


def create_async_session(settings: Settings):
    """Create an async SQLAlchemy session factory for PostgreSQL.
    
    Args:
        settings: Application settings containing database configuration
        
    Returns:
        An async SQLAlchemy session factory
    """
    # Construct the PostgreSQL connection string
    connection_string = (
        f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    
    # Create an async engine
    engine = create_async_engine(
        connection_string,
        echo=settings.debug,
        future=True,
    )
    
    # Create a session factory
    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    # Return the session factory
    return async_session_factory
