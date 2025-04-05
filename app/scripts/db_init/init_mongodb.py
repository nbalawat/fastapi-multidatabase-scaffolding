"""Initialize the MongoDB database with required collections and indexes."""
import asyncio
import logging
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models.users import Role
from app.models.permissions import DEFAULT_ROLE_PERMISSIONS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_collections(client: AsyncIOMotorClient, db_name: str) -> None:
    """Create required collections and indexes in MongoDB.
    
    Args:
        client: MongoDB client
        db_name: Database name
    """
    db = client[db_name]
    collection_names = await db.list_collection_names()
    
    # Create users collection if it doesn't exist
    if "users" not in collection_names:
        logger.info("Creating users collection")
        await db.create_collection("users")
    
    # Create indexes for users collection
    users = db.users
    
    # Create unique indexes for username and email
    logger.info("Creating indexes for users collection")
    await users.create_index("username", unique=True)
    await users.create_index("email", unique=True)
    
    # Create index for role for faster role-based queries
    await users.create_index("role")
    
    # Create notes collection if it doesn't exist
    if "notes" not in collection_names:
        logger.info("Creating notes collection")
        await db.create_collection("notes")
    
    # Create indexes for notes collection
    notes = db.notes
    
    # Create indexes for notes collection
    logger.info("Creating indexes for notes collection")
    await notes.create_index("user_id")
    await notes.create_index("visibility")
    await notes.create_index("tags")
    
    # Create roles collection if it doesn't exist
    if "roles" not in collection_names:
        logger.info("Creating roles collection")
        await db.create_collection("roles")
    
    # Create indexes for roles collection
    roles = db.roles
    
    # Create unique index for role name
    logger.info("Creating indexes for roles collection")
    await roles.create_index("name", unique=True)
    
    logger.info("MongoDB collections and indexes created successfully")


async def create_admin_user(client: AsyncIOMotorClient, db_name: str) -> None:
    """Create an admin user if it doesn't exist.
    
    Args:
        client: MongoDB client
        db_name: Database name
    """
    db = client[db_name]
    users = db.users
    
    # Check if admin user exists
    admin_user = await users.find_one({"username": get_settings().admin_username})
    
    if admin_user is None:
        logger.info("Creating admin user")
        
        # Create admin user
        admin_data: Dict[str, Any] = {
            "username": get_settings().admin_username,
            "email": get_settings().admin_email,
            "full_name": "Administrator",
            "role": Role.ADMIN.value,
            "hashed_password": get_password_hash(get_settings().admin_password),
            "is_active": True
        }
        
        # Insert admin user
        await users.insert_one(admin_data)
        logger.info("Admin user created successfully")
    else:
        logger.info("Admin user already exists")


async def create_default_roles(client: AsyncIOMotorClient, db_name: str) -> None:
    """Create default roles if they don't exist.
    
    Args:
        client: MongoDB client
        db_name: Database name
    """
    db = client[db_name]
    roles = db.roles
    
    # Check and create default roles
    for role_name, role_data in DEFAULT_ROLE_PERMISSIONS.items():
        # Check if role exists
        existing_role = await roles.find_one({"name": role_name})
        
        if existing_role is None:
            logger.info(f"Creating default role: {role_name}")
            
            # Convert permissions set to list for storage
            role_dict = role_data.model_dump()
            role_dict["permissions"] = [p.value for p in role_dict["permissions"]]
            
            # Insert role
            await roles.insert_one(role_dict)
            logger.info(f"Default role {role_name} created successfully")
        else:
            logger.info(f"Default role {role_name} already exists")


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=30))
async def init_mongodb() -> None:
    """Initialize MongoDB database with retry mechanism."""
    settings = get_settings()
    
    # Create MongoDB connection string
    if settings.mongodb_connection_string:
        connection_string = settings.mongodb_connection_string
    else:
        # Construct the MongoDB connection string based on whether auth is needed
        if settings.db_user and settings.db_password:
            # Connection with authentication
            connection_string = (
                f"mongodb://{settings.db_user}:{settings.db_password}"
                f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
                f"?authSource=admin"
            )
        else:
            # Connection without authentication
            connection_string = (
                f"mongodb://{settings.db_host}:{settings.db_port}/{settings.db_name}"
            )
    
    # Connect to MongoDB with improved connection options
    logger.info(f"Connecting to MongoDB at {settings.db_host}:{settings.db_port}")
    client = AsyncIOMotorClient(
        connection_string,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000
    )
    
    try:
        # Check connection
        await client.admin.command("ping")
        logger.info("Connected to MongoDB successfully")
        
        # Initialize database
        await create_collections(client, settings.db_name)
        await create_admin_user(client, settings.db_name)
        await create_default_roles(client, settings.db_name)
        
        logger.info("MongoDB initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing MongoDB: {e}")
        raise
    finally:
        # Close connection
        client.close()


if __name__ == "__main__":
    asyncio.run(init_mongodb())
