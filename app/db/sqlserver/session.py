"""SQL Server session management."""
from typing import Callable, Any, AsyncGenerator, Dict, Optional, Union, List
import asyncio
import os
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, URL, text as sa_text
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.result import Result, ChunkedIteratorResult

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class AsyncResultWrapper:
    """Wrapper for SQLAlchemy Result to provide async-compatible interface."""
    
    def __init__(self, result: Result):
        self.result = result
    
    def first(self):
        """Get the first row."""
        return self.result.first()
    
    def scalar(self):
        """Get the first column of the first row."""
        return self.result.scalar()
    
    def scalar_one(self):
        """Get the first column of the first row, raising if no rows found."""
        return self.result.scalar_one()
    
    def mappings(self):
        """Return an iterator of dictionaries."""
        return self.result.mappings()
    
    def all(self):
        """Return all rows."""
        return self.result.all()
    
    @property
    def rowcount(self):
        """Return the number of rows affected."""
        return self.result.rowcount


class AsyncSessionWrapper:
    """Wrapper class to provide async interface for sync SQLAlchemy session."""
    
    def __init__(self, session: Session):
        self.session = session
    
    async def execute(self, statement, params=None, **kwargs):
        """Execute a statement asynchronously."""
        def _execute():
            if isinstance(statement, TextClause) and params is not None:
                result = self.session.execute(statement, params, **kwargs)
            else:
                result = self.session.execute(statement, **kwargs)
            return AsyncResultWrapper(result)
        return await asyncio.to_thread(_execute)
    
    async def commit(self):
        """Commit the transaction asynchronously."""
        def _commit():
            return self.session.commit()
        return await asyncio.to_thread(_commit)
    
    async def rollback(self):
        """Rollback the transaction asynchronously."""
        def _rollback():
            return self.session.rollback()
        return await asyncio.to_thread(_rollback)
    
    async def close(self):
        """Close the session asynchronously."""
        def _close():
            return self.session.close()
        return await asyncio.to_thread(_close)
    
    def __getattr__(self, name):
        """Delegate attribute access to the underlying session."""
        return getattr(self.session, name)
    
    # Context manager support
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        await self.close()


def create_async_session(settings: Settings, use_master_db: bool = False) -> Callable[[], AsyncSessionWrapper]:
    """Create a SQL Server session factory.
    
    Args:
        settings: Application settings
        use_master_db: If True, connect to the master database instead of the specified database.
                      This is useful for creating the database if it doesn't exist.
        
    Returns:
        A session factory that creates AsyncSessionWrapper instances
    """
    # In Docker, use the service name instead of localhost
    host = settings.sqlserver_host
    if host == "localhost" and os.path.exists("/.dockerenv"):
        host = "sqlserver"  # Use the service name from docker-compose
        logger.info(f"Running in Docker, using host: {host}")
    
    # For initial setup, connect to master database
    database = "master" if use_master_db else settings.sqlserver_db
    
    logger.info(f"Creating SQL Server session factory for {host}:{settings.sqlserver_port}/{database}")
    
    # Construct connection URL
    connection_url = URL.create(
        drivername="mssql+pymssql",
        username=settings.sqlserver_user,
        password=settings.sqlserver_password,
        host=host,
        port=settings.sqlserver_port,
        database=database,
    )
    
    # Create the sync engine
    engine = create_engine(
        connection_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    
    # Create the sync session factory
    sync_session_factory = sessionmaker(engine, expire_on_commit=False)
    
    # Create an async wrapper for the sync session
    def get_async_session() -> AsyncSession:
        sync_session = sync_session_factory()
        return AsyncSessionWrapper(sync_session)
    
    return get_async_session
