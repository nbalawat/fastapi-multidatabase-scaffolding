"""Test script for Role-Based Access Control (RBAC) system with PostgreSQL."""
import pytest
from app.scripts.tests.test_rbac import test_rbac_system


@pytest.fixture
def base_url() -> str:
    """Provide the base URL for PostgreSQL API."""
    return "http://localhost:8000"  # PostgreSQL port


async def test_postgres_rbac_system(base_url) -> None:
    """Test the RBAC system with PostgreSQL."""
    await test_rbac_system(base_url)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
