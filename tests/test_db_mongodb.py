import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

from app.core.config import Settings
from app.db.mongodb.adapter import MongoDBAdapter


@pytest.fixture
def mock_collection():
    """Create a mock MongoDB collection."""
    collection = AsyncMock(spec=AsyncIOMotorCollection)
    return collection


@pytest.fixture
def mock_db():
    """Create a mock MongoDB database."""
    db = AsyncMock(spec=AsyncIOMotorDatabase)
    return db


@pytest.fixture
def mock_client():
    """Create a mock MongoDB client."""
    client = AsyncMock(spec=AsyncIOMotorClient)
    return client


@pytest.fixture
def mongodb_adapter(mock_client, mock_db, mock_collection):
    """Create a MongoDB adapter with mocked components."""
    # Mock the client creation
    with patch("app.db.mongodb.adapter.AsyncIOMotorClient") as mock_client_class:
        mock_client_class.return_value = mock_client
        
        # Mock the database access
        mock_client.__getitem__.return_value = mock_db
        
        # Mock the collection access
        mock_db.__getitem__.return_value = mock_collection
        
        # Create the adapter with test settings
        settings = Settings(
            db_host="test_host",
            db_port=27017,
            db_user="test_user",
            db_password="test_password",
            db_name="test_db"
        )
        adapter = MongoDBAdapter(settings)
        
        # Store the mocks for assertions
        adapter._mock_client = mock_client
        adapter._mock_db = mock_db
        adapter._mock_collection = mock_collection
        
        yield adapter


@pytest.mark.asyncio
async def test_mongodb_connect_disconnect(mongodb_adapter, mock_client):
    """Test connecting to and disconnecting from MongoDB."""
    # Test connect
    await mongodb_adapter.connect()
    assert mongodb_adapter._client is not None
    
    # Test disconnect
    await mongodb_adapter.disconnect()
    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_mongodb_create(mongodb_adapter, mock_collection):
    """Test creating a document in MongoDB."""
    await mongodb_adapter.connect()
    
    # Setup mock for insert_one
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId("60d5ec47d39e3e3b5c732f08")
    mock_collection.insert_one.return_value = mock_result
    
    # Setup mock for find_one
    mock_collection.find_one.return_value = {
        "_id": ObjectId("60d5ec47d39e3e3b5c732f08"),
        "name": "Test",
        "value": 42
    }
    
    # Test create
    result = await mongodb_adapter.create("test_collection", {"name": "Test", "value": 42})
    
    # Verify result
    assert result["id"] == "60d5ec47d39e3e3b5c732f08"
    assert result["name"] == "Test"
    assert result["value"] == 42
    
    # Verify insert_one was called with the correct data
    mock_collection.insert_one.assert_called_once()
    
    # Verify find_one was called to get the inserted document
    mock_collection.find_one.assert_called_once()


@pytest.mark.asyncio
async def test_mongodb_read(mongodb_adapter, mock_collection):
    """Test reading a document from MongoDB."""
    await mongodb_adapter.connect()
    
    # Setup mock for find_one
    mock_collection.find_one.return_value = {
        "_id": ObjectId("60d5ec47d39e3e3b5c732f08"),
        "name": "Test",
        "value": 42
    }
    
    # Test read with ObjectId string
    result = await mongodb_adapter.read("test_collection", "60d5ec47d39e3e3b5c732f08")
    
    # Verify result
    assert result["id"] == "60d5ec47d39e3e3b5c732f08"
    assert result["name"] == "Test"
    assert result["value"] == 42
    
    # Verify find_one was called with the correct filter
    mock_collection.find_one.assert_called_once()
    
    # Reset mock
    mock_collection.find_one.reset_mock()
    
    # Test read with non-ObjectId ID (should try username lookup)
    mock_collection.find_one.return_value = {
        "_id": ObjectId("60d5ec47d39e3e3b5c732f09"),
        "username": "testuser",
        "email": "test@example.com"
    }
    
    result = await mongodb_adapter.read("test_collection", "testuser")
    
    # Verify result
    assert result["id"] == "60d5ec47d39e3e3b5c732f09"
    assert result["username"] == "testuser"
    
    # Verify find_one was called with the correct filter
    mock_collection.find_one.assert_called_once()


@pytest.mark.asyncio
async def test_mongodb_update(mongodb_adapter, mock_collection):
    """Test updating a document in MongoDB."""
    await mongodb_adapter.connect()
    
    # Setup mock for find_one_and_update
    mock_collection.find_one_and_update.return_value = {
        "_id": ObjectId("60d5ec47d39e3e3b5c732f08"),
        "name": "Test",
        "value": 99  # Updated value
    }
    
    # Test update
    result = await mongodb_adapter.update("test_collection", "60d5ec47d39e3e3b5c732f08", {"value": 99})
    
    # Verify result
    assert result["id"] == "60d5ec47d39e3e3b5c732f08"
    assert result["name"] == "Test"
    assert result["value"] == 99
    
    # Verify find_one_and_update was called with the correct parameters
    mock_collection.find_one_and_update.assert_called_once()


@pytest.mark.asyncio
async def test_mongodb_delete(mongodb_adapter, mock_collection):
    """Test deleting a document from MongoDB."""
    await mongodb_adapter.connect()
    
    # Setup mock for delete_one
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_collection.delete_one.return_value = mock_result
    
    # Test delete
    result = await mongodb_adapter.delete("test_collection", "60d5ec47d39e3e3b5c732f08")
    
    # Verify result
    assert result is True
    
    # Verify delete_one was called with the correct filter
    mock_collection.delete_one.assert_called_once()
    
    # Reset mock
    mock_collection.delete_one.reset_mock()
    
    # Test delete with no document found
    mock_result.deleted_count = 0
    mock_collection.delete_one.return_value = mock_result
    
    result = await mongodb_adapter.delete("test_collection", "nonexistent")
    
    # Verify result
    assert result is False
    
    # Verify delete_one was called with the correct filter
    mock_collection.delete_one.assert_called_once()


@pytest.mark.asyncio
async def test_mongodb_list(mongodb_adapter, mock_collection):
    """Test listing documents from MongoDB."""
    await mongodb_adapter.connect()
    
    # Setup mock for find
    mock_cursor = AsyncMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list.return_value = [
        {
            "_id": ObjectId("60d5ec47d39e3e3b5c732f08"),
            "name": "Test 1",
            "value": 42
        },
        {
            "_id": ObjectId("60d5ec47d39e3e3b5c732f09"),
            "name": "Test 2",
            "value": 99
        }
    ]
    mock_collection.find.return_value = mock_cursor
    
    # Test list
    result = await mongodb_adapter.list("test_collection", skip=0, limit=10)
    
    # Verify result
    assert len(result) == 2
    assert result[0]["id"] == "60d5ec47d39e3e3b5c732f08"
    assert result[0]["name"] == "Test 1"
    assert result[1]["id"] == "60d5ec47d39e3e3b5c732f09"
    assert result[1]["name"] == "Test 2"
    
    # Verify find was called
    mock_collection.find.assert_called_once()
    
    # Verify skip and limit were called with the correct parameters
    mock_cursor.skip.assert_called_once_with(0)
    mock_cursor.limit.assert_called_once_with(10)
