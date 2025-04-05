"""Test script for SQL Server CRUD operations."""
import asyncio
import pytest
import httpx
from typing import Optional

from app.scripts.tests.test_crud_base import BaseCrudTests

# SQL Server API runs on port 8002
PORT = 8002
DB_TYPE = "sqlserver"

# Initialize the base test class
crud_tests = BaseCrudTests(port=PORT, db_type=DB_TYPE)


@pytest.fixture
async def client():
    """Create an async HTTP client."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
async def admin_token(client):
    """Get admin token for testing."""
    token = await crud_tests.login(client, "admin", "admin123")
    if not token:
        pytest.skip("Admin login failed")
    return token


@pytest.fixture
async def user_token(client):
    """Get regular user token for testing."""
    token = await crud_tests.login(client, "user", "user123")
    if not token:
        pytest.skip("User login failed")
    return token


@pytest.mark.asyncio
async def test_sqlserver_health(client):
    """Test SQL Server health endpoint."""
    await crud_tests.test_health(client)


@pytest.mark.asyncio
async def test_sqlserver_notes_crud(client, admin_token):
    """Test CRUD operations for notes in SQL Server."""
    await crud_tests.test_notes_crud(client, admin_token)


@pytest.mark.asyncio
async def test_sqlserver_notes_listing(client, admin_token):
    """Test notes listing with SQL Server."""
    await crud_tests.test_notes_listing(client, admin_token)


@pytest.mark.asyncio
async def test_sqlserver_user_management(client, admin_token):
    """Test user management with SQL Server."""
    await crud_tests.test_user_management(client, admin_token)


if __name__ == "__main__":
    # Run pytest directly, not through asyncio.run
    pytest.main(["-xvs", __file__])
