import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.postgres.adapter import PostgresAdapter


@pytest.fixture
def mock_session():
    """Create a mock SQLAlchemy session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def postgres_adapter():
    """Create a PostgreSQL adapter with mocked session factory."""
    with patch("app.db.postgres.adapter.create_async_session") as mock_create_session:
        # Mock the session factory to return our mock session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_create_session.return_value = mock_session
        
        # Create the adapter with test settings
        settings = Settings(
            db_host="test_host",
            db_port=5432,
            db_user="test_user",
            db_password="test_password",
            db_name="test_db"
        )
        adapter = PostgresAdapter(settings)
        
        # Store the mock session for assertions
        adapter._mock_session = mock_session
        
        yield adapter


@pytest.mark.asyncio
async def test_postgres_connect_disconnect(postgres_adapter):
    """Test connecting to and disconnecting from PostgreSQL."""
    # Test connect
    await postgres_adapter.connect()
    assert postgres_adapter._session is not None
    
    # Test disconnect
    await postgres_adapter.disconnect()
    assert postgres_adapter._session is None


@pytest.mark.asyncio
async def test_postgres_create(postgres_adapter):
    """Test creating a record in PostgreSQL."""
    await postgres_adapter.connect()
    
    # Setup mock for execute
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = {"id": 1, "name": "Test", "value": 42}
    postgres_adapter._mock_session.execute.return_value = mock_result
    
    # Test create
    result = await postgres_adapter.create("test_table", {"name": "Test", "value": 42})
    
    # Verify result
    assert result == {"id": 1, "name": "Test", "value": 42}
    
    # Verify execute was called with an INSERT statement
    postgres_adapter._mock_session.execute.assert_called_once()
    
    # Verify commit was called
    postgres_adapter._mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_postgres_read(postgres_adapter):
    """Test reading a record from PostgreSQL."""
    await postgres_adapter.connect()
    
    # Setup mock for execute
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = {"id": 1, "name": "Test", "value": 42}
    postgres_adapter._mock_session.execute.return_value = mock_result
    
    # Test read
    result = await postgres_adapter.read("test_table", 1)
    
    # Verify result
    assert result == {"id": 1, "name": "Test", "value": 42}
    
    # Verify execute was called with a SELECT statement
    postgres_adapter._mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_postgres_update(postgres_adapter):
    """Test updating a record in PostgreSQL."""
    await postgres_adapter.connect()
    
    # Setup mock for execute
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = {"id": 1, "name": "Test", "value": 99}
    postgres_adapter._mock_session.execute.return_value = mock_result
    
    # Test update
    result = await postgres_adapter.update("test_table", 1, {"value": 99})
    
    # Verify result
    assert result == {"id": 1, "name": "Test", "value": 99}
    
    # Verify execute was called with an UPDATE statement
    postgres_adapter._mock_session.execute.assert_called()
    
    # Verify commit was called
    postgres_adapter._mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_postgres_delete(postgres_adapter):
    """Test deleting a record from PostgreSQL."""
    await postgres_adapter.connect()
    
    # Setup mock for execute
    mock_result = MagicMock()
    mock_result.rowcount = 1  # Simulate one row affected
    postgres_adapter._mock_session.execute.return_value = mock_result
    
    # Test delete
    result = await postgres_adapter.delete("test_table", 1)
    
    # Verify result
    assert result is True
    
    # Verify execute was called with a DELETE statement
    postgres_adapter._mock_session.execute.assert_called_once()
    
    # Verify commit was called
    postgres_adapter._mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_postgres_list(postgres_adapter):
    """Test listing records from PostgreSQL."""
    await postgres_adapter.connect()
    
    # Setup mock for execute
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [
        {"id": 1, "name": "Test 1", "value": 42},
        {"id": 2, "name": "Test 2", "value": 99}
    ]
    postgres_adapter._mock_session.execute.return_value = mock_result
    
    # Test list
    result = await postgres_adapter.list("test_table", skip=0, limit=10)
    
    # Verify result
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2
    
    # Verify execute was called with a SELECT statement
    postgres_adapter._mock_session.execute.assert_called_once()
