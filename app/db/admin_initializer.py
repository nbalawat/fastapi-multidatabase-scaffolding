"""
Admin user initialization module.

This module provides functionality to create admin users across different database types.
It leverages the schema registry and database adapters for a clean, DRY approach.
"""
from typing import Dict, Any, Optional
import logging
import asyncio
from uuid import uuid4
from datetime import datetime

from app.core.config import get_settings, Settings
from app.core.security import get_password_hash
from app.db.base import DatabaseAdapter, DatabaseAdapterFactory
from app.models.users.model import Role, UserCreate, UserInDB
from app.db.schema_registry import get_schema_registry

logger = logging.getLogger(__name__)

async def create_admin_user(db_adapter: Optional[DatabaseAdapter] = None) -> None:
    """Create an admin user if one doesn't exist.
    
    Args:
        db_adapter: Optional database adapter. If not provided, one will be created.
    """
    settings = get_settings()
    close_adapter = False
    
    try:
        # Get or create database adapter
        if db_adapter is None:
            db_adapter = DatabaseAdapterFactory.get_adapter(settings.db_type)
            await db_adapter.connect()
            close_adapter = True
            
        logger.info(f"Creating admin user for {settings.db_type} database")
        
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
        admin_user = UserCreate(
            email=settings.admin_email,
            username=settings.admin_username,
            password=settings.admin_password,
            full_name="Admin User",
            role=Role.ADMIN
        )
        
        # Convert to UserInDB
        user_in_db = UserInDB(
            **admin_user.dict(exclude={"password", "is_active"}),
            hashed_password=get_password_hash(admin_user.password),
            id=str(uuid4()),
            is_active=True,
            created_at=datetime.now()
        )
        
        # Get the schema for users model
        schema_registry = get_schema_registry()
        schema = schema_registry.get_schema("users", db_adapter.db_type)
        
        # Convert to database model if schema exists
        db_data = user_in_db.dict()
        if schema:
            db_data = schema.to_db_model(db_data)
        
        # Create the user
        await db_adapter.create(collection="users", data=db_data)
        logger.info(f"Created admin user: {settings.admin_username}")
    
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise
    
    finally:
        # Disconnect from the database if we created the adapter
        if close_adapter and db_adapter:
            await db_adapter.disconnect()

async def initialize_admin_users() -> None:
    """Initialize admin users for all configured database types."""
    settings = get_settings()
    
    # Get all configured database types
    db_types = []
    
    # Always include the primary database type
    db_types.append(settings.db_type)
    
    # Add additional database types if configured
    if hasattr(settings, "additional_db_types") and settings.additional_db_types:
        db_types.extend(settings.additional_db_types)
    
    # Create admin users for each database type
    for db_type in db_types:
        try:
            db_adapter = DatabaseAdapterFactory.get_adapter(db_type)
            await db_adapter.connect()
            
            try:
                await create_admin_user(db_adapter)
            finally:
                await db_adapter.disconnect()
                
        except Exception as e:
            logger.error(f"Error initializing admin user for {db_type}: {e}")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the initialization
    asyncio.run(initialize_admin_users())
