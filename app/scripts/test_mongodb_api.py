"""Test script for MongoDB API endpoints."""
import asyncio
import logging
import httpx
import json
import pytest
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"


@pytest.fixture
async def client():
    """Create an async HTTP client."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
async def admin_token(client):
    """Get admin token for testing."""
    token = await login(client, "admin", "admin123")
    if not token:
        pytest.skip("Admin login failed")
    return token


@pytest.fixture
async def user_token(client):
    """Get test user token for testing."""
    # Create a test user if needed
    test_user = {
        "username": "noteuser",
        "email": "noteuser@example.com",
        "password": "password123",
        "full_name": "Note User"
    }
    
    # Register test user
    register_response = await client.post(
        f"{BASE_URL}{API_PREFIX}/register",
        json=test_user
    )
    
    if register_response.status_code not in [201, 400]:
        pytest.skip(f"Registration failed: {register_response.status_code}")
    
    # Login as test user
    token = await login(client, test_user["username"], test_user["password"])
    if not token:
        pytest.skip("Test user login failed")
    
    return token


async def test_mongodb_api() -> None:
    """Test the MongoDB API endpoints."""
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
        
        # Create a test user if needed
        test_user = {
            "username": "noteuser",
            "email": "noteuser@example.com",
            "password": "password123",
            "full_name": "Note User"
        }
        
        # Register test user
        register_response = await client.post(
            f"{BASE_URL}{API_PREFIX}/register",
            json=test_user
        )
        
        if register_response.status_code == 201:
            logger.info(f"User registered: {test_user['username']}")
        elif register_response.status_code == 400:
            logger.info(f"User {test_user['username']} already exists")
        else:
            logger.error(f"Registration failed: {register_response.status_code} - {register_response.text}")
            return
        
        # Login as test user
        user_token = await login(client, test_user["username"], test_user["password"])
        
        if not user_token:
            logger.error("Test user login failed")
            return
        
        logger.info(f"Login successful for user: {test_user['username']}")
        
        # Test notes API with MongoDB
        await test_notes_api(client, user_token)
        
        # Test admin endpoints
        await test_admin_endpoints(client, admin_token)
        
        logger.info("MongoDB API test completed successfully!")


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


@pytest.mark.asyncio
async def test_notes_api(client: httpx.AsyncClient, user_token: str) -> None:
    """Test the notes API endpoints.
    
    Args:
        client: HTTP client
        token: Access token
    """
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create a note
    note_data = {
        "title": "Test Note",
        "content": "This is a test note created by the MongoDB integration test",
        "visibility": "private",
        "tags": ["test", "mongodb"]
    }
    
    create_response = await client.post(
        f"{BASE_URL}{API_PREFIX}/notes",
        json=note_data,
        headers=headers
    )
    
    if create_response.status_code != 201:
        logger.error(f"Failed to create note: {create_response.status_code} - {create_response.text}")
        return
    
    note = create_response.json()
    note_id = note["id"]
    logger.info(f"Created note with ID: {note_id}")
    
    # Get the note
    get_response = await client.get(
        f"{BASE_URL}{API_PREFIX}/notes/{note_id}",
        headers=headers
    )
    
    if get_response.status_code != 200:
        logger.error(f"Failed to get note: {get_response.status_code} - {get_response.text}")
        return
    
    logger.info(f"Retrieved note: {get_response.json()['title']}")
    
    # Update the note
    update_data = {
        "title": "Updated Test Note",
        "content": "This note has been updated"
    }
    
    update_response = await client.put(
        f"{BASE_URL}{API_PREFIX}/notes/{note_id}",
        json=update_data,
        headers=headers
    )
    
    if update_response.status_code != 200:
        logger.error(f"Failed to update note: {update_response.status_code} - {update_response.text}")
        return
    
    logger.info(f"Updated note: {update_response.json()['title']}")
    
    # List notes
    list_response = await client.get(
        f"{BASE_URL}{API_PREFIX}/notes",
        headers=headers
    )
    
    if list_response.status_code != 200:
        logger.error(f"Failed to list notes: {list_response.status_code} - {list_response.text}")
        return
    
    notes = list_response.json()
    logger.info(f"Listed {len(notes)} notes")
    
    # Delete the note
    delete_response = await client.delete(
        f"{BASE_URL}{API_PREFIX}/notes/{note_id}",
        headers=headers
    )
    
    if delete_response.status_code != 204:
        logger.error(f"Failed to delete note: {delete_response.status_code} - {delete_response.text}")
        return
    
    logger.info(f"Deleted note with ID: {note_id}")


@pytest.mark.asyncio
async def test_admin_endpoints(client: httpx.AsyncClient, admin_token: str) -> None:
    """Test the admin endpoints.
    
    Args:
        client: HTTP client
        token: Admin access token
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test admin endpoint to list all notes
    admin_response = await client.get(
        f"{BASE_URL}{API_PREFIX}/notes/admin/notes",
        headers=headers
    )
    
    if admin_response.status_code != 200:
        logger.error(f"Failed to access admin endpoint: {admin_response.status_code} - {admin_response.text}")
        return
    
    notes = admin_response.json()
    logger.info(f"Admin endpoint: Listed {len(notes)} notes")


if __name__ == "__main__":
    asyncio.run(test_mongodb_api())
