#!/usr/bin/env python
"""
SQL Server database cleanup script.
Cleans up test data from the SQL Server database.
"""
import asyncio
import logging
import os
import pymssql

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.sqlserver.session import create_async_session, sa_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)


async def clean_test_data() -> None:
    """Clean up test data from the database."""
    settings = get_settings()
    logger.info(f"Connecting to SQL Server database: {settings.sqlserver_db} on {settings.sqlserver_host}:{settings.sqlserver_port}")
    
    try:
        # Get the session factory
        session_factory = create_async_session(settings)
        session = session_factory()
        
        try:
            # Delete test data from the notes table first (due to foreign key constraints)
            logger.info("Deleting test data from notes table...")
            await session.execute(
                sa_text("""
                DELETE FROM notes 
                WHERE user_id LIKE 'testuser%' OR user_id LIKE 'noteuser%'
                """)
            )
            await session.commit()
            
            # Delete test data from the users table
            logger.info("Deleting test data from users table...")
            await session.execute(
                sa_text("""
                DELETE FROM users 
                WHERE username LIKE 'testuser%' OR username LIKE 'noteuser%'
                """)
            )
            await session.commit()
            
            # Delete test data from the items table
            logger.info("Deleting test data from items table...")
            await session.execute(
                sa_text("""
                DELETE FROM items 
                WHERE 1=1
                """)
            )
            await session.commit()
            
            logger.info("Test data cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error cleaning up test data: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
    
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


async def main() -> None:
    """Main entry point."""
    logger.info("Starting SQL Server test data cleanup...")
    await clean_test_data()
    logger.info("SQL Server test data cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
