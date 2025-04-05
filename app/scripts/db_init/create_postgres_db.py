#!/usr/bin/env python
"""
PostgreSQL database creation script.
Creates the database if it doesn't exist.
"""
import asyncio
import logging
import sys
from typing import Optional

import asyncpg

from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_database() -> None:
    """Create the PostgreSQL database if it doesn't exist."""
    settings = get_settings()
    
    # Connect to the default 'postgres' database to create our application database
    try:
        # Connect to the default database
        conn = await asyncpg.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database="postgres"  # Connect to default database
        )
        
        # Check if our database exists
        row = await conn.fetchrow(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            settings.db_name
        )
        
        if not row:
            # Database doesn't exist, create it
            logger.info(f"Creating database '{settings.db_name}'...")
            await conn.execute(f"CREATE DATABASE {settings.db_name}")
            logger.info(f"Database '{settings.db_name}' created successfully")
        else:
            logger.info(f"Database '{settings.db_name}' already exists")
            
        # Close the connection
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_database())
