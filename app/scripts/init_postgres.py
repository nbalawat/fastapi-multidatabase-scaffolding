#!/usr/bin/env python
"""
PostgreSQL database initialization script.
Creates tables and an admin user if they don't exist.
"""
import asyncio
import logging
from typing import Dict, Any

from sqlalchemy import text

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.postgres.session import create_async_session
from app.models.users import Role

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables() -> None:
    """Create database tables if they don't exist."""
    settings = get_settings()
    logger.info(f"Connecting to PostgreSQL database: {settings.db_name} on {settings.db_host}:{settings.db_port}")
    
    try:
        # Get the session factory
        session_factory = create_async_session(settings)
        
        # Read SQL script
        try:
            # Try with absolute path first
            script_path = "/app/app/scripts/init_tables.sql"
            logger.info(f"Attempting to read SQL script from {script_path}")
            with open(script_path, "r") as f:
                sql_script = f.read()
        except FileNotFoundError:
            # Fall back to relative path
            script_path = "app/scripts/init_tables.sql"
            logger.info(f"Falling back to relative path: {script_path}")
            with open(script_path, "r") as f:
                sql_script = f.read()
        
        logger.info(f"Successfully read SQL script from {script_path}")
        
        # Split SQL script into individual statements
        # Split on semicolons but ignore those in comments
        sql_statements = []
        current_statement = []
        for line in sql_script.split('\n'):
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('--'):
                current_statement.append(line)
                if line_stripped.endswith(';'):
                    sql_statements.append('\n'.join(current_statement))
                    current_statement = []
        
        # Add any remaining statement
        if current_statement:
            sql_statements.append('\n'.join(current_statement))
        
        # Execute each SQL statement separately
        logger.info(f"Executing {len(sql_statements)} SQL statements to create tables...")
        async with session_factory() as session:
            for i, statement in enumerate(sql_statements, 1):
                if statement.strip():
                    try:
                        logger.info(f"Executing statement {i}/{len(sql_statements)}")
                        await session.execute(text(statement))
                        await session.commit()
                    except Exception as e:
                        logger.error(f"Error executing statement {i}: {e}")
                        logger.error(f"Statement: {statement}")
                        raise
            
        logger.info("Database tables created successfully")
    
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


async def init_postgres() -> None:
    """Initialize the PostgreSQL database."""
    logger.info("Initializing PostgreSQL database...")
    
    # Create tables
    await create_tables()
    
    logger.info("PostgreSQL database initialization complete")


if __name__ == "__main__":
    asyncio.run(init_postgres())
