"""Test script for MongoDB integration and RBAC system."""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings
from app.db.mongodb.adapter import MongoDBAdapter
from app.models.permissions import Permission, RolePermissions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mongodb_connection() -> None:
    """Test connection to MongoDB."""
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_connection_string)
    
    try:
        # The ismaster command is cheap and does not require auth
        await client.admin.command('ismaster')
        logger.info("MongoDB connection successful!")
        return client
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        return None


async def test_mongodb_adapter() -> None:
    """Test the MongoDB adapter."""
    # Create MongoDB adapter
    adapter = MongoDBAdapter()
    
    try:
        # Connect to MongoDB
        await adapter.connect()
        logger.info("MongoDB adapter connected successfully!")
        
        # Test collections exist
        db = adapter.client[adapter.database_name]
        collections = await db.list_collection_names()
        logger.info(f"Collections in database: {collections}")
        
        required_collections = ["users", "notes", "roles"]
        for collection in required_collections:
            if collection in collections:
                logger.info(f"✓ Collection '{collection}' exists")
            else:
                logger.error(f"✗ Collection '{collection}' does not exist")
        
        # Test CRUD operations
        test_data = {
            "name": "Test Document",
            "description": "This is a test document",
            "tags": ["test", "mongodb", "integration"]
        }
        
        # Create
        created = await adapter.create("test_collection", test_data)
        logger.info(f"Created document: {created}")
        
        # Read
        doc_id = created["id"]
        read = await adapter.read("test_collection", doc_id)
        logger.info(f"Read document: {read}")
        
        # Update
        update_data = {"description": "Updated description"}
        updated = await adapter.update("test_collection", doc_id, update_data)
        logger.info(f"Updated document: {updated}")
        
        # List
        documents = await adapter.list("test_collection")
        logger.info(f"Listed {len(documents)} documents")
        
        # Delete
        deleted = await adapter.delete("test_collection", doc_id)
        logger.info(f"Deleted document: {deleted}")
        
        # Disconnect
        await adapter.disconnect()
        logger.info("MongoDB adapter disconnected successfully!")
        
    except Exception as e:
        logger.error(f"MongoDB adapter test failed: {e}")


async def test_roles_in_mongodb() -> None:
    """Test role management in MongoDB."""
    # Create MongoDB adapter
    adapter = MongoDBAdapter()
    
    try:
        # Connect to MongoDB
        await adapter.connect()
        logger.info("Connected to MongoDB for role testing")
        
        # List roles
        roles = await adapter.list("roles")
        logger.info(f"Found {len(roles)} roles in MongoDB")
        
        # Check if default roles exist
        default_roles = ["admin", "user", "guest"]
        for role_name in default_roles:
            role = await adapter.read("roles", role_name)
            if role:
                logger.info(f"✓ Default role '{role_name}' exists with permissions: {role.get('permissions', [])}")
            else:
                logger.error(f"✗ Default role '{role_name}' does not exist")
        
        # Create a test role
        test_role = {
            "name": "tester",
            "description": "Role for testing purposes",
            "permissions": [
                Permission.NOTE_READ,
                Permission.NOTE_CREATE,
                Permission.USER_READ
            ]
        }
        
        # Check if role already exists
        existing_role = await adapter.read("roles", "tester")
        if existing_role:
            logger.info("Test role 'tester' already exists, updating it")
            await adapter.update("roles", "tester", test_role)
        else:
            logger.info("Creating test role 'tester'")
            await adapter.create("roles", test_role)
        
        # Verify the role was created/updated
        created_role = await adapter.read("roles", "tester")
        logger.info(f"Test role: {created_role}")
        
        # Clean up - delete the test role
        await adapter.delete("roles", "tester")
        logger.info("Deleted test role 'tester'")
        
        # Disconnect
        await adapter.disconnect()
        logger.info("Disconnected from MongoDB")
        
    except Exception as e:
        logger.error(f"Role testing failed: {e}")


async def test_user_permissions() -> None:
    """Test user permissions in MongoDB."""
    # Create MongoDB adapter
    adapter = MongoDBAdapter()
    
    try:
        # Connect to MongoDB
        await adapter.connect()
        logger.info("Connected to MongoDB for permission testing")
        
        # Get admin user
        admin_user = await adapter.read("users", "admin")
        if not admin_user:
            logger.error("Admin user not found")
            return
        
        logger.info(f"Admin user found: {admin_user.get('username')}")
        
        # Get admin role
        admin_role = await adapter.read("roles", "admin")
        if not admin_role:
            logger.error("Admin role not found")
            return
        
        logger.info(f"Admin role has permissions: {admin_role.get('permissions', [])}")
        
        # Check if admin has all permissions
        all_permissions = [p for p in dir(Permission) if not p.startswith('_')]
        missing_permissions = []
        
        for permission in all_permissions:
            permission_value = getattr(Permission, permission)
            if permission_value not in admin_role.get('permissions', []):
                missing_permissions.append(permission_value)
        
        if missing_permissions:
            logger.warning(f"Admin role is missing permissions: {missing_permissions}")
        else:
            logger.info("✓ Admin role has all permissions")
        
        # Disconnect
        await adapter.disconnect()
        logger.info("Disconnected from MongoDB")
        
    except Exception as e:
        logger.error(f"Permission testing failed: {e}")


async def main() -> None:
    """Run all MongoDB integration tests."""
    logger.info("Starting MongoDB integration tests...")
    
    # Test MongoDB connection
    client = await test_mongodb_connection()
    if not client:
        logger.error("MongoDB connection test failed, aborting further tests")
        return
    
    # Run tests
    await test_mongodb_adapter()
    await test_roles_in_mongodb()
    await test_user_permissions()
    
    logger.info("MongoDB integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
