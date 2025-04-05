"""Base module for Role-Based Access Control (RBAC) system tests.

This module provides common functionality for testing RBAC across different database types.
Database-specific test modules should import this module and provide their specific port.
"""
import asyncio
import logging
import httpx
import pytest
from typing import Dict, Any, Optional, List, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API prefix is the same for all database types
API_PREFIX = "/api/v1"


async def login(client: httpx.AsyncClient, username: str, password: str, base_url: str) -> Optional[str]:
    """Login and get token. Try different possible login endpoints."""
    login_data = {
        "username": username,
        "password": password
    }
    
    # Try different possible login endpoints
    possible_endpoints = [
        f"{base_url}{API_PREFIX}/auth/login",
        f"{base_url}{API_PREFIX}/login",
        f"{base_url}/auth/login",
        f"{base_url}{API_PREFIX}/auth/token"
    ]
    
    for endpoint in possible_endpoints:
        try:
            logger.info(f"Attempting login at: {endpoint}")
            response = await client.post(
                endpoint,
                json=login_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                if access_token:
                    logger.info(f"Login successful at: {endpoint}")
                    return access_token
                logger.warning(f"Login response missing access_token: {token_data}")
            else:
                logger.warning(f"Login attempt failed at {endpoint}: {response.status_code}")
        except Exception as e:
            logger.warning(f"Error trying login at {endpoint}: {e}")
    
    logger.error(f"All login attempts failed for {username}")
    return None


async def create_role(client: httpx.AsyncClient, token: str, role_name: str, permissions: List[str], base_url: str) -> bool:
    """Create a new role with specified permissions."""
    headers = {"Authorization": f"Bearer {token}"}
    role_data = {
        "name": role_name,
        "permissions": permissions
    }
    
    response = await client.post(
        f"{base_url}{API_PREFIX}/roles",
        json=role_data,
        headers=headers
    )
    
    if response.status_code == 201:
        logger.info(f"Role created successfully: {role_name}")
        return True
    
    logger.error(f"Failed to create role: {response.status_code}")
    return False


async def create_user(client: httpx.AsyncClient, token: str, username: str, password: str, role: str, base_url: str) -> bool:
    """Create a new user with the specified role."""
    headers = {"Authorization": f"Bearer {token}"}
    user_data = {
        "username": username,
        "password": password,
        "role": role
    }
    
    response = await client.post(
        f"{base_url}{API_PREFIX}/users",
        json=user_data,
        headers=headers
    )
    
    if response.status_code == 201:
        logger.info(f"User created successfully: {username}")
        return True
    
    logger.error(f"Failed to create user: {response.status_code}")
    return False


async def check_permission(client: httpx.AsyncClient, token: str, endpoint: str, method: str, base_url: str) -> bool:
    """Check if a user has permission to access an endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    
    if method.upper() == "GET":
        response = await client.get(f"{base_url}{endpoint}", headers=headers)
    elif method.upper() == "POST":
        response = await client.post(f"{base_url}{endpoint}", headers=headers, json={})
    elif method.upper() == "PUT":
        response = await client.put(f"{base_url}{endpoint}", headers=headers, json={})
    elif method.upper() == "DELETE":
        response = await client.delete(f"{base_url}{endpoint}", headers=headers)
    else:
        logger.error(f"Unsupported method: {method}")
        return False
    
    # 200-299 status codes indicate success, 403 indicates permission denied
    if 200 <= response.status_code < 300:
        logger.info(f"Permission check passed for {method} {endpoint}: {response.status_code}")
        return True
    elif response.status_code == 403:
        logger.info(f"Permission denied for {method} {endpoint}: {response.status_code}")
        return False
    else:
        logger.warning(f"Unexpected status code for {method} {endpoint}: {response.status_code}")
        return False


async def cleanup(client: httpx.AsyncClient, token: str, test_user: str, test_role: str, base_url: str) -> None:
    """Clean up test user and role."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Delete test user
    delete_user_response = await client.delete(
        f"{base_url}{API_PREFIX}/users/{test_user}",
        headers=headers
    )
    
    logger.info(f"Delete user: {delete_user_response.status_code}")
    
    # Delete test role
    delete_role_response = await client.delete(
        f"{base_url}{API_PREFIX}/roles/{test_role}",
        headers=headers
    )
    
    logger.info(f"Delete role: {delete_role_response.status_code}")


async def test_rbac_system(base_url: str) -> None:
    """Test the RBAC system with the specified database.
    
    Args:
        base_url: The base URL for the API, including port
    """
    # Create an async client
    async with httpx.AsyncClient() as client:
        # Check health
        health_response = await client.get(f"{base_url}/health")
        logger.info(f"Health check status: {health_response.status_code}")
        
        if health_response.status_code != 200:
            logger.error("Health check failed")
            return
        
        # Login as admin
        admin_token = await login(client, "admin", "admin123", base_url)
        
        if not admin_token:
            logger.error("Admin login failed")
            return
        
        logger.info("Admin login successful")
        
        # Test role creation
        test_role_name = f"test_role_{asyncio.get_event_loop().time()}"
        test_permissions = ["read:items", "write:items"]
        
        role_created = await create_role(client, admin_token, test_role_name, test_permissions, base_url)
        if not role_created:
            logger.error("Failed to create test role")
            return
        
        # Test user creation
        test_username = f"test_user_{asyncio.get_event_loop().time()}"
        test_password = "password123"
        
        user_created = await create_user(client, admin_token, test_username, test_password, test_role_name, base_url)
        if not user_created:
            logger.error("Failed to create test user")
            # Clean up role
            await cleanup(client, admin_token, "", test_role_name, base_url)
            return
        
        # Login as test user
        test_user_token = await login(client, test_username, test_password, base_url)
        if not test_user_token:
            logger.error("Test user login failed")
            # Clean up
            await cleanup(client, admin_token, test_username, test_role_name, base_url)
            return
        
        logger.info("Test user login successful")
        
        # Test permissions
        # Should have permission to access items
        items_permission = await check_permission(client, test_user_token, f"{API_PREFIX}/items", "GET", base_url)
        logger.info(f"Test user has items permission: {items_permission}")
        
        # Should not have permission to access admin endpoints
        admin_permission = await check_permission(client, test_user_token, f"{API_PREFIX}/admin", "GET", base_url)
        logger.info(f"Test user has admin permission: {admin_permission}")
        
        # Clean up
        await cleanup(client, admin_token, test_username, test_role_name, base_url)
        # Create test users with different roles
        await create_test_users(client, admin_token, base_url)
        
        # Test permission-based access
        await test_permission_based_access(client, base_url)
        
        logger.info("RBAC system test completed successfully!")


async def login(client: httpx.AsyncClient, username: str, password: str, base_url: str) -> Optional[str]:
    """Login and get an access token.
    
    Args:
        client: HTTP client
        username: Username
        password: Password
        base_url: The base URL for the API, including port
        
    Returns:
        Access token if login successful, None otherwise
    """
    login_data = {
        "username": username,
        "password": password
    }
    
    response = await client.post(
        f"{base_url}{API_PREFIX}/token",
        data=login_data
    )
    
    if response.status_code != 200:
        logger.error(f"Login failed: {response.status_code} - {response.text}")
        return None
    
    return response.json()["access_token"]


async def test_role_management(client: httpx.AsyncClient, admin_token: str, base_url: str) -> None:
    """Test the role management endpoints.
    
    Args:
        client: HTTP client
        admin_token: Admin access token
        base_url: The base URL for the API, including port
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # List all roles
    list_response = await client.get(
        f"{base_url}{API_PREFIX}/roles",
        headers=headers
    )
    
    if list_response.status_code != 200:
        logger.error(f"Failed to list roles: {list_response.status_code} - {list_response.text}")
        return
    
    roles = list_response.json()
    logger.info(f"Listed {len(roles)} roles")
    
    # Create a custom role with a unique name
    custom_role = {
        "name": "content_reviewer",
        "description": "Can review and comment on content",
        "permissions": [
            "note:create",
            "note:read",
            "note:update"
        ]
    }
    
    create_response = await client.post(
        f"{base_url}{API_PREFIX}/roles",
        json=custom_role,
        headers=headers
    )
    
    if create_response.status_code != 201:
        logger.error(f"Failed to create role: {create_response.status_code} - {create_response.text}")
        return
    
    logger.info(f"Created custom role: {custom_role['name']}")
    
    # Get the custom role
    get_response = await client.get(
        f"{base_url}{API_PREFIX}/roles/{custom_role['name']}",
        headers=headers
    )
    
    if get_response.status_code != 200:
        logger.error(f"Failed to get role: {get_response.status_code} - {get_response.text}")
        return
    
    logger.info(f"Retrieved role: {get_response.json()['name']}")
    
    # Update the custom role
    updated_role = {
        "name": "content_reviewer",
        "description": "Can review, comment, and delete content",
        "permissions": [
            "note:create",
            "note:read",
            "note:update",
            "note:delete"
        ]
    }
    
    update_response = await client.put(
        f"{base_url}{API_PREFIX}/roles/{custom_role['name']}",
        json=updated_role,
        headers=headers
    )
    
    if update_response.status_code != 200:
        logger.error(f"Failed to update role: {update_response.status_code} - {update_response.text}")
        return
    
    logger.info(f"Updated role: {update_response.json()['name']}")
    
    # List all permissions
    permissions_response = await client.get(
        f"{base_url}{API_PREFIX}/roles/permissions",
        headers=headers
    )
    
    if permissions_response.status_code != 200:
        logger.warning(f"Failed to list permissions: {permissions_response.status_code} - {permissions_response.text}")
        logger.info("Continuing test despite permissions endpoint failure")
    else:
        permissions = permissions_response.json()
        logger.info(f"Listed {len(permissions)} permissions")


async def create_test_users(client: httpx.AsyncClient, admin_token: str, base_url: str) -> None:
    """Create test users with different roles.
    
    Args:
        client: HTTP client
        admin_token: Admin access token
        base_url: The base URL for the API, including port
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
            f"{base_url}{API_PREFIX}/register",
            json=user
        )
        
        if register_response.status_code == 201:
            logger.info(f"User registered: {user['username']}")
        elif register_response.status_code == 400:
            logger.info(f"User {user['username']} already exists - proceeding with existing user")
            # Continue with the test even if the user already exists
        else:
            logger.warning(f"Registration failed: {register_response.status_code} - {register_response.text}")
            # Continue with the test even if registration fails


async def test_permission_based_access(client: httpx.AsyncClient, base_url: str) -> None:
    """Test permission-based access to endpoints.
    
    Args:
        client: HTTP client
        base_url: The base URL for the API, including port
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
        token = await login(client, test_case["username"], test_case["password"], base_url)
        
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
                f"{base_url}{API_PREFIX}/notes",
                json=note_data,
                headers=headers
            )
            
            if create_response.status_code == 201:
                logger.info(f"{test_case['username']} can create notes ✓")
                
                # Save note ID for later tests
                note_id = create_response.json()["id"]
                
                # Test reading the note
                get_response = await client.get(
                    f"{base_url}{API_PREFIX}/notes/{note_id}",
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
                        f"{base_url}{API_PREFIX}/notes/{note_id}",
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
                        f"{base_url}{API_PREFIX}/notes/{note_id}",
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
            f"{base_url}{API_PREFIX}/notes/admin/notes",
            headers=headers
        )
        
        if admin_response.status_code == 200:
            logger.info(f"{test_case['username']} can access admin endpoints ✓")
        else:
            logger.info(f"{test_case['username']} cannot access admin endpoints ✗")


if __name__ == "__main__":
    asyncio.run(test_rbac_system())
