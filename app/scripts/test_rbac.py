"""Test script for Role-Based Access Control (RBAC) system."""
import asyncio
import logging
import httpx
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"


async def test_rbac_system() -> None:
    """Test the RBAC system with MongoDB."""
    # Create an async client
    async with httpx.AsyncClient() as client:
        # Check health
        health_response = await client.get(f"{BASE_URL}/health")
        logger.info(f"Health check status: {health_response.status_code}")
        
        if health_response.status_code != 200:
            logger.error("Health check failed")
            return
        
        # Login as admin
        admin_token = await login(client, "admin", "admin123")
        
        if not admin_token:
            logger.error("Admin login failed")
            return
        
        logger.info("Login successful for user: admin")
        
        # Test role management endpoints
        await test_role_management(client, admin_token)
        
        # Create test users with different roles
        await create_test_users(client, admin_token)
        
        # Test permission-based access
        await test_permission_based_access(client)
        
        logger.info("RBAC system test completed successfully!")


async def login(client: httpx.AsyncClient, username: str, password: str) -> Optional[str]:
    """Login and get an access token.
    
    Args:
        client: HTTP client
        username: Username
        password: Password
        
    Returns:
        Access token if login successful, None otherwise
    """
    login_data = {
        "username": username,
        "password": password
    }
    
    response = await client.post(
        f"{BASE_URL}{API_PREFIX}/token",
        data=login_data
    )
    
    if response.status_code != 200:
        logger.error(f"Login failed: {response.status_code} - {response.text}")
        return None
    
    return response.json()["access_token"]


async def test_role_management(client: httpx.AsyncClient, admin_token: str) -> None:
    """Test the role management endpoints.
    
    Args:
        client: HTTP client
        admin_token: Admin access token
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # List all roles
    list_response = await client.get(
        f"{BASE_URL}{API_PREFIX}/roles",
        headers=headers
    )
    
    if list_response.status_code != 200:
        logger.error(f"Failed to list roles: {list_response.status_code} - {list_response.text}")
        return
    
    roles = list_response.json()
    logger.info(f"Listed {len(roles)} roles")
    
    # Create a custom role
    editor_role = {
        "name": "editor",
        "description": "Can create and edit content",
        "permissions": [
            "note:create",
            "note:read",
            "note:update"
        ]
    }
    
    create_response = await client.post(
        f"{BASE_URL}{API_PREFIX}/roles",
        json=editor_role,
        headers=headers
    )
    
    if create_response.status_code != 201:
        logger.error(f"Failed to create role: {create_response.status_code} - {create_response.text}")
        return
    
    logger.info(f"Created custom role: {editor_role['name']}")
    
    # Get the custom role
    get_response = await client.get(
        f"{BASE_URL}{API_PREFIX}/roles/{editor_role['name']}",
        headers=headers
    )
    
    if get_response.status_code != 200:
        logger.error(f"Failed to get role: {get_response.status_code} - {get_response.text}")
        return
    
    logger.info(f"Retrieved role: {get_response.json()['name']}")
    
    # Update the custom role
    updated_role = {
        "name": "editor",
        "description": "Can create, edit, and delete content",
        "permissions": [
            "note:create",
            "note:read",
            "note:update",
            "note:delete"
        ]
    }
    
    update_response = await client.put(
        f"{BASE_URL}{API_PREFIX}/roles/{editor_role['name']}",
        json=updated_role,
        headers=headers
    )
    
    if update_response.status_code != 200:
        logger.error(f"Failed to update role: {update_response.status_code} - {update_response.text}")
        return
    
    logger.info(f"Updated role: {update_response.json()['name']}")
    
    # List all permissions
    permissions_response = await client.get(
        f"{BASE_URL}{API_PREFIX}/roles/permissions",
        headers=headers
    )
    
    if permissions_response.status_code != 200:
        logger.error(f"Failed to list permissions: {permissions_response.status_code} - {permissions_response.text}")
        return
    
    permissions = permissions_response.json()
    logger.info(f"Listed {len(permissions)} permissions")


async def create_test_users(client: httpx.AsyncClient, admin_token: str) -> None:
    """Create test users with different roles.
    
    Args:
        client: HTTP client
        admin_token: Admin access token
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test users with different roles
    test_users = [
        {
            "username": "editoruser",
            "email": "editor@example.com",
            "password": "password123",
            "full_name": "Editor User",
            "role": "editor"
        },
        {
            "username": "regularuser",
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Regular User",
            "role": "user"
        },
        {
            "username": "guestuser",
            "email": "guest@example.com",
            "password": "password123",
            "full_name": "Guest User",
            "role": "guest"
        }
    ]
    
    # Register test users
    for user in test_users:
        register_response = await client.post(
            f"{BASE_URL}{API_PREFIX}/register",
            json=user
        )
        
        if register_response.status_code == 201:
            logger.info(f"User registered: {user['username']}")
        elif register_response.status_code == 400:
            logger.info(f"User {user['username']} already exists")
        else:
            logger.error(f"Registration failed: {register_response.status_code} - {register_response.text}")


async def test_permission_based_access(client: httpx.AsyncClient) -> None:
    """Test permission-based access to endpoints.
    
    Args:
        client: HTTP client
    """
    # Test users and their expected permissions
    test_cases = [
        {
            "username": "editoruser",
            "password": "password123",
            "can_create_note": True,
            "can_read_note": True,
            "can_update_note": True,
            "can_delete_note": True,
            "can_access_admin": False
        },
        {
            "username": "regularuser",
            "password": "password123",
            "can_create_note": True,
            "can_read_note": True,
            "can_update_note": True,
            "can_delete_note": True,
            "can_access_admin": False
        },
        {
            "username": "guestuser",
            "password": "password123",
            "can_create_note": False,
            "can_read_note": True,
            "can_update_note": False,
            "can_delete_note": False,
            "can_access_admin": False
        },
        {
            "username": "admin",
            "password": "admin123",
            "can_create_note": True,
            "can_read_note": True,
            "can_update_note": True,
            "can_delete_note": True,
            "can_access_admin": True
        }
    ]
    
    for test_case in test_cases:
        # Login as test user
        token = await login(client, test_case["username"], test_case["password"])
        
        if not token:
            logger.error(f"Login failed for {test_case['username']}")
            continue
        
        logger.info(f"Testing permissions for user: {test_case['username']}")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test creating a note
        if test_case["can_create_note"]:
            note_data = {
                "title": f"Test Note by {test_case['username']}",
                "content": "This is a test note",
                "visibility": "private",
                "tags": ["test"]
            }
            
            create_response = await client.post(
                f"{BASE_URL}{API_PREFIX}/notes",
                json=note_data,
                headers=headers
            )
            
            if create_response.status_code == 201:
                logger.info(f"{test_case['username']} can create notes ✓")
                
                # Save note ID for later tests
                note_id = create_response.json()["id"]
                
                # Test reading the note
                get_response = await client.get(
                    f"{BASE_URL}{API_PREFIX}/notes/{note_id}",
                    headers=headers
                )
                
                if get_response.status_code == 200:
                    logger.info(f"{test_case['username']} can read notes ✓")
                else:
                    logger.info(f"{test_case['username']} cannot read notes ✗")
                
                # Test updating the note
                if test_case["can_update_note"]:
                    update_data = {
                        "title": f"Updated Note by {test_case['username']}",
                        "content": "This note has been updated"
                    }
                    
                    update_response = await client.put(
                        f"{BASE_URL}{API_PREFIX}/notes/{note_id}",
                        json=update_data,
                        headers=headers
                    )
                    
                    if update_response.status_code == 200:
                        logger.info(f"{test_case['username']} can update notes ✓")
                    else:
                        logger.info(f"{test_case['username']} cannot update notes ✗")
                
                # Test deleting the note
                if test_case["can_delete_note"]:
                    delete_response = await client.delete(
                        f"{BASE_URL}{API_PREFIX}/notes/{note_id}",
                        headers=headers
                    )
                    
                    if delete_response.status_code == 204:
                        logger.info(f"{test_case['username']} can delete notes ✓")
                    else:
                        logger.info(f"{test_case['username']} cannot delete notes ✗")
            else:
                logger.info(f"{test_case['username']} cannot create notes ✗")
        
        # Test accessing admin endpoint
        admin_response = await client.get(
            f"{BASE_URL}{API_PREFIX}/notes/admin/notes",
            headers=headers
        )
        
        if admin_response.status_code == 200:
            logger.info(f"{test_case['username']} can access admin endpoints ✓")
        else:
            logger.info(f"{test_case['username']} cannot access admin endpoints ✗")


if __name__ == "__main__":
    asyncio.run(test_rbac_system())
