import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.mysql.adapter import MySQLAdapter


@pytest.fixture
def mock_session():
    """Create a mock SQLAlchemy session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mysql_adapter():
    """Create a MySQL adapter with mocked session factory."""
    with patch("app.db.mysql.adapter.create_async_session") as mock_create_session:
        # Mock the session factory to return our mock session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_create_session.return_value = mock_session
        
        # Create the adapter with test settings
        settings = Settings(
            db_host="test_host",
            db_port=3306,
            db_user="test_user",
            db_password="test_password",
            db_name="test_db"
        )
        adapter = MySQLAdapter(settings)
        
        # Store the mock session for assertions
        adapter._mock_session = mock_session
        
        yield adapter


@pytest.mark.asyncio
async def test_mysql_connect_disconnect(mysql_adapter):
    """Test connecting to and disconnecting from MySQL."""
    # Test connect
    await mysql_adapter.connect()
    assert mysql_adapter._session is not None
    
    # Test disconnect
    await mysql_adapter.disconnect()
    assert mysql_adapter._session is None


@pytest.mark.asyncio
async def test_mysql_create(mysql_adapter):
    """Test creating a record in MySQL."""
    await mysql_adapter.connect()
    
    # Setup mock for execute
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = {"id": 1, "name": "Test", "value": 42}
    mysql_adapter._mock_session.execute.return_value = mock_result
    
    # Test create
    result = await mysql_adapter.create("test_table", {"name": "Test", "value": 42})
    
    # Verify result
    assert result == {"id": 1, "name": "Test", "value": 42}
    
    # Verify execute was called with an INSERT statement
    mysql_adapter._mock_session.execute.assert_called_once()
    
    # Verify commit was called
    mysql_adapter._mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_mysql_read(mysql_adapter):
    """Test reading a record from MySQL."""
    await mysql_adapter.connect()
    
    # Setup mock for execute
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = {"id": 1, "name": "Test", "value": 42}
    mysql_adapter._mock_session.execute.return_value = mock_result
    
    # Test read
    result = await mysql_adapter.read("test_table", 1)
    
    # Verify result
    assert result == {"id": 1, "name": "Test", "value": 42}
    
    # Verify execute was called with a SELECT statement
    mysql_adapter._mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_mysql_update(mysql_adapter):
    """Test updating a record in MySQL."""
    await mysql_adapter.connect()
    
    # Setup mock for execute
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = {"id": 1, "name": "Test", "value": 99}
    mysql_adapter._mock_session.execute.return_value = mock_result
    
    # Test update
    result = await mysql_adapter.update("test_table", 1, {"value": 99})
    
    # Verify result
    assert result == {"id": 1, "name": "Test", "value": 99}
    
    # Verify execute was called with an UPDATE statement
    mysql_adapter._mock_session.execute.assert_called()
    
    # Verify commit was called
    mysql_adapter._mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_mysql_delete(mysql_adapter):
    """Test deleting a record from MySQL."""
    await mysql_adapter.connect()
    
    # Setup mock for execute
    mock_result = MagicMock()
    mock_result.rowcount = 1  # Simulate one row affected
    mysql_adapter._mock_session.execute.return_value = mock_result
    
    # Test delete
    result = await mysql_adapter.delete("test_table", 1)
    
    # Verify result
    assert result is True
    
    # Verify execute was called with a DELETE statement
    mysql_adapter._mock_session.execute.assert_called_once()
    
    # Verify commit was called
    mysql_adapter._mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_mysql_list(mysql_adapter):
    """Test listing records from MySQL."""
    await mysql_adapter.connect()
    
    # Setup mock for execute
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [
        {"id": 1, "name": "Test 1", "value": 42},
        {"id": 2, "name": "Test 2", "value": 99}
    ]
    mysql_adapter._mock_session.execute.return_value = mock_result
    
    # Test list
    result = await mysql_adapter.list("test_table", skip=0, limit=10)
    
    # Verify result
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2
    
    # Verify execute was called with a SELECT statement
    mysql_adapter._mock_session.execute.assert_called_once()
