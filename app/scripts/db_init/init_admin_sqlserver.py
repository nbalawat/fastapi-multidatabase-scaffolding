#!/usr/bin/env python
"""
Initialize SQL Server database with an admin user.
This script is used for development and testing purposes.
"""
import asyncio
import logging
from typing import Dict, Any

from sqlalchemy import text

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.sqlserver.session import create_async_session
from app.models.users import Role

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_admin_user() -> None:
    """Create an admin user if it doesn't exist."""
    settings = get_settings()
    logger.info("Creating admin user if it doesn't exist...")
    
    try:
        # Get the session factory
        session_factory = create_async_session(settings)
        
        # Check if admin user exists
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM users WHERE username = :username"),
                {"username": settings.admin_username}
            )
            count = result.scalar()
            
            if count == 0:
                # Create admin user
                hashed_password = get_password_hash(settings.admin_password)
                
                await session.execute(
                    text("""
                    INSERT INTO users (username, email, hashed_password, full_name, disabled, role)
                    VALUES (:username, :email, :hashed_password, :full_name, :disabled, :role)
                    """),
                    {
                        "username": settings.admin_username,
                        "email": settings.admin_email,
                        "hashed_password": hashed_password,
                        "full_name": "Administrator",
                        "disabled": False,
                        "role": Role.ADMIN.value
                    }
                )
                await session.commit()
                logger.info(f"Admin user '{settings.admin_username}' created successfully")
            else:
                logger.info(f"Admin user '{settings.admin_username}' already exists")
    
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    asyncio.run(create_admin_user())
