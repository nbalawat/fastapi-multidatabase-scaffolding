"""Test script for Role-Based Access Control (RBAC) system with MongoDB."""
import pytest
from app.scripts.tests.test_rbac import test_rbac_system


@pytest.fixture
def base_url() -> str:
    """Provide the base URL for MongoDB API."""
    return "http://localhost:8001"  # MongoDB port


async def test_mongodb_rbac_system(base_url) -> None:
    """Test the RBAC system with MongoDB."""
    await test_rbac_system(base_url)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
