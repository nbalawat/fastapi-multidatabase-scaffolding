#!/usr/bin/env python
"""
Database initialization script.
Creates an admin user if one doesn't exist.
"""
import asyncio
import logging
from typing import Dict, Any

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.base import DatabaseAdapterFactory
from app.models.users import Role

# Import all database adapters to register them with the factory
from app.db.postgres.adapter import PostgresAdapter
from app.db.mysql.adapter import MySQLAdapter
from app.db.mongodb.adapter import MongoDBAdapter
from app.db.sqlserver.adapter import SQLServerAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_admin_user() -> None:
    """Create an admin user if one doesn't exist."""
    settings = get_settings()
    logger.info(f"Using database type: {settings.db_type}")
    logger.info(f"Database connection details: host={settings.db_host}, port={settings.db_port}, user={settings.db_user}")
    
    try:
        db_adapter = DatabaseAdapterFactory.get_adapter(settings.db_type)
        logger.info(f"Successfully created adapter for {settings.db_type}")
    except Exception as e:
        logger.error(f"Failed to create database adapter: {e}")
        # List available adapters
        logger.info(f"Available adapters: {', '.join(DatabaseAdapterFactory.get_registered_adapters())}")
        raise
    
    # Connect to the database
    try:
        await db_adapter.connect()
        logger.info("Successfully connected to the database")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise
    
    try:
        # Check if admin user exists
        admin_users = await db_adapter.list(
            collection="users",
            skip=0,
            limit=1,
            query={"email": settings.admin_email}
        )
        
        if admin_users:
            logger.info("Admin user already exists")
            return
        
        # Create admin user
        admin_user: Dict[str, Any] = {
            "email": settings.admin_email,
            "username": settings.admin_username,
            "hashed_password": get_password_hash(settings.admin_password),
            "full_name": "Admin User",
            "disabled": False,
            "role": Role.ADMIN.value
        }
        
        await db_adapter.create(collection="users", data=admin_user)
        logger.info(f"Created admin user: {settings.admin_username}")
    
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise
    
    finally:
        # Disconnect from the database
        await db_adapter.disconnect()


async def init_db() -> None:
    """Initialize the database."""
    logger.info("Initializing database...")
    
    # Create admin user
    await create_admin_user()
    
    logger.info("Database initialization complete")


if __name__ == "__main__":
    asyncio.run(init_db())
