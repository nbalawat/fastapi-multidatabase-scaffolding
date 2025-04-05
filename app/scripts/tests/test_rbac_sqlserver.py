"""Test script for Role-Based Access Control (RBAC) system with SQL Server."""
import pytest
from app.scripts.tests.test_rbac import test_rbac_system


@pytest.fixture
def base_url() -> str:
    """Provide the base URL for SQL Server API."""
    return "http://localhost:8002"  # SQL Server port


async def test_sqlserver_rbac_system(base_url) -> None:
    """Test the RBAC system with SQL Server."""
    await test_rbac_system(base_url)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
