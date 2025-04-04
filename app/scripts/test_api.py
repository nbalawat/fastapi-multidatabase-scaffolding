#!/usr/bin/env python
"""
Test script for API authentication and database connections.
This script can be run to verify that the API is working correctly.
"""
import asyncio
import logging
from typing import Dict, Any, Optional

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://localhost:8000"


async def test_health() -> bool:
    """Test the health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        logger.info(f"Health check status: {response.status_code}")
        return response.status_code == 200


async def login(username: str, password: str) -> Optional[str]:
    """Login to the API and get an access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            logger.info(f"Login successful for user: {username}")
            return token
        else:
            logger.error(f"Login failed: {response.status_code} - {response.text}")
            return None


async def register_user(email: str, username: str, password: str, full_name: str) -> bool:
    """Register a new user."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                "full_name": full_name
            }
        )
        if response.status_code == 201:
            logger.info(f"User registered: {username}")
            return True
        else:
            logger.error(f"Registration failed: {response.status_code} - {response.text}")
            return False


async def get_users(token: str) -> Optional[Dict[str, Any]]:
    """Get the list of users."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/users/",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Got {len(data)} users")
            return data
        else:
            logger.error(f"Failed to get users: {response.status_code} - {response.text}")
            return None


async def test_api_flow() -> None:
    """Test the complete API flow."""
    # Test health endpoint
    if not await test_health():
        logger.error("Health check failed")
        return
    
    # Test admin login
    admin_token = await login("admin", "admin123")
    if not admin_token:
        logger.error("Admin login failed")
        return
    
    # Test getting users with admin token
    users = await get_users(admin_token)
    if not users:
        logger.error("Failed to get users with admin token")
        return
    
    # Test registering a new user
    test_user = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass",
        "full_name": "Test User"
    }
    
    if not await register_user(**test_user):
        logger.error("Failed to register test user")
        return
    
    # Test login with new user
    user_token = await login(test_user["username"], test_user["password"])
    if not user_token:
        logger.error("Test user login failed")
        return
    
    logger.info("API flow test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_api_flow())
