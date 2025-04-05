#!/usr/bin/env python
"""
SQL Server database initialization script.
Creates tables and an admin user if they don't exist.
"""
import asyncio
import logging
import os
import pymssql
from pathlib import Path
from typing import Dict, Any

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.core.logging import get_logger
from app.db.sqlserver.session import create_async_session, sa_text
from app.models.users import Role

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)


async def create_tables() -> None:
    """Create database tables if they don't exist."""
    try:
        settings = get_settings()
        logger.info(f"Connecting to SQL Server database: {settings.sqlserver_db} on {settings.sqlserver_host}:{settings.sqlserver_port}")
        
        # For database creation, we'll use a direct pymssql connection instead of SQLAlchemy
        # to avoid transaction issues
        host = settings.sqlserver_host
        if host == "localhost" and os.path.exists("/.dockerenv"):
            host = "sqlserver"  # Use the service name from docker-compose
            
        logger.info(f"Connecting to SQL Server master database on {host}:{settings.sqlserver_port}")
        
        # Add robust retry mechanism
        max_retries = 30
        retry_count = 0
        retry_delay = 5  # seconds
        
        while retry_count < max_retries:
            try:
                logger.info(f"Connection attempt {retry_count + 1}/{max_retries}")
                # Use direct pymssql connection for database operations
                conn = pymssql.connect(
                    server=host,
                    port=settings.sqlserver_port,
                    user=settings.sqlserver_user,
                    password=settings.sqlserver_password,
                    database="master",  # Connect to master database
                    autocommit=True,  # Important for CREATE DATABASE
                    login_timeout=30  # Set login timeout to 30 seconds
                )
                logger.info("Successfully connected to SQL Server")
                break
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Failed to connect to SQL Server after {max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Connection attempt failed: {str(e)}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
        
        try:
            cursor = conn.cursor()
            # Check if database exists
            cursor.execute("SELECT COUNT(*) FROM sys.databases WHERE name = %s", (settings.sqlserver_db,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.info(f"Creating database {settings.sqlserver_db}")
                cursor.execute(f"CREATE DATABASE {settings.sqlserver_db}")
                logger.info(f"Database {settings.sqlserver_db} created successfully")
            else:
                logger.info(f"Database {settings.sqlserver_db} already exists")
                
            cursor.close()
        finally:
            conn.close()
            
        # Now connect to our database for table creation
        session_factory = create_async_session(settings)
        
        # Read SQL script
        try:
            # Try with absolute path first
            script_path = "/app/app/scripts/db_init/init_tables_sqlserver.sql"
            logger.info(f"Attempting to read SQL script from {script_path}")
            with open(script_path, "r") as f:
                sql_script = f.read()
        except FileNotFoundError:
            # Try another absolute path
            try:
                script_path = "/app/app/scripts/init_tables_sqlserver.sql"
                logger.info(f"Trying alternative path: {script_path}")
                with open(script_path, "r") as f:
                    sql_script = f.read()
            except FileNotFoundError:
                # Fall back to relative paths
                try:
                    script_path = "app/scripts/db_init/init_tables_sqlserver.sql"
                    logger.info(f"Trying relative path: {script_path}")
                    with open(script_path, "r") as f:
                        sql_script = f.read()
                except FileNotFoundError:
                    # Last attempt
                    script_path = "app/scripts/init_tables_sqlserver.sql"
                    logger.info(f"Final attempt with path: {script_path}")
                    with open(script_path, "r") as f:
                        sql_script = f.read()
        
        logger.info(f"Successfully read SQL script from {script_path}")
        
        # Split SQL script into individual statements
        # SQL Server uses GO as a batch separator
        sql_statements = []
        current_statement = []
        for line in sql_script.split('\n'):
            line_stripped = line.strip()
            if line_stripped == 'GO':
                if current_statement:
                    sql_statements.append('\n'.join(current_statement))
                    current_statement = []
            elif line_stripped and not line_stripped.startswith('--'):
                current_statement.append(line)
        
        # Add any remaining statement
        if current_statement:
            sql_statements.append('\n'.join(current_statement))
        
        # Execute each SQL statement separately
        logger.info(f"Executing {len(sql_statements)} SQL statements to create tables...")
        session = session_factory()
        try:
            for i, statement in enumerate(sql_statements, 1):
                if statement.strip():
                    try:
                        logger.info(f"Executing statement {i}/{len(sql_statements)}")
                        await session.execute(sa_text(statement))
                        await session.commit()
                    except Exception as e:
                        logger.error(f"Error executing statement {i}: {e}")
                        logger.error(f"Statement: {statement}")
                        await session.rollback()
                        raise
            logger.info("Database tables created successfully")
        finally:
            await session.close()
            
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


async def create_admin_user() -> None:
    """Create an admin user if it doesn't exist."""
    settings = get_settings()
    logger.info("Creating admin user if it doesn't exist...")
    
    try:
        # Get the session factory
        session_factory = create_async_session(settings)
        
        # Check if admin user exists
        session = session_factory()
        try:
            result = await session.execute(
                sa_text("SELECT COUNT(*) FROM users WHERE username = :username"),
                {"username": settings.admin_username}
            )
            count = result.scalar()
            
            if count == 0:
                # Create admin user
                hashed_password = get_password_hash(settings.admin_password)
                
                await session.execute(
                    sa_text("""
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
        finally:
            await session.close()
    
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


async def init_sqlserver() -> None:
    """Initialize the SQL Server database."""
    logger.info("Initializing SQL Server database...")
    
    # Create tables
    await create_tables()
    
    # Create admin user
    await create_admin_user()
    
    logger.info("SQL Server database initialization complete")


if __name__ == "__main__":
    asyncio.run(init_sqlserver())
