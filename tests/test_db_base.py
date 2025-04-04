import pytest
from typing import Any, Dict, List, Optional

from app.db.base import DatabaseAdapter, DatabaseAdapterFactory


# Mock database adapter for testing
class MockDatabaseAdapter(DatabaseAdapter):
    def __init__(self):
        self.connected = False
        self.data: Dict[str, List[Dict[str, Any]]] = {}
        
    async def connect(self) -> None:
        self.connected = True
        
    async def disconnect(self) -> None:
        self.connected = False
        
    async def create(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if collection not in self.data:
            self.data[collection] = []
        data_with_id = {**data, "id": len(self.data[collection]) + 1}
        self.data[collection].append(data_with_id)
        return data_with_id
        
    async def read(self, collection: str, id: Any) -> Optional[Dict[str, Any]]:
        if collection not in self.data:
            return None
        for item in self.data[collection]:
            if item.get("id") == id:
                return item
        return None
        
    async def update(self, collection: str, id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if collection not in self.data:
            return None
        for i, item in enumerate(self.data[collection]):
            if item.get("id") == id:
                updated_item = {**item, **data}
                self.data[collection][i] = updated_item
                return updated_item
        return None
        
    async def delete(self, collection: str, id: Any) -> bool:
        if collection not in self.data:
            return False
        for i, item in enumerate(self.data[collection]):
            if item.get("id") == id:
                del self.data[collection][i]
                return True
        return False
        
    async def list(self, collection: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        if collection not in self.data:
            return []
        return self.data[collection][skip:skip + limit]


# Register the mock adapter with the factory
DatabaseAdapterFactory.register("mock", MockDatabaseAdapter)


@pytest.fixture
def db_adapter():
    adapter = MockDatabaseAdapter()
    return adapter


@pytest.mark.asyncio
async def test_db_adapter_connect_disconnect(db_adapter):
    assert db_adapter.connected is False
    await db_adapter.connect()
    assert db_adapter.connected is True
    await db_adapter.disconnect()
    assert db_adapter.connected is False


@pytest.mark.asyncio
async def test_db_adapter_crud_operations(db_adapter):
    await db_adapter.connect()
    
    # Test create
    test_data = {"name": "Test Item", "value": 42}
    created = await db_adapter.create("test_collection", test_data)
    assert created["id"] == 1
    assert created["name"] == "Test Item"
    assert created["value"] == 42
    
    # Test read
    read_item = await db_adapter.read("test_collection", 1)
    assert read_item is not None
    assert read_item["id"] == 1
    assert read_item["name"] == "Test Item"
    
    # Test update
    updated = await db_adapter.update("test_collection", 1, {"value": 99})
    assert updated["value"] == 99
    assert updated["name"] == "Test Item"  # Original field preserved
    
    # Test list
    items = await db_adapter.list("test_collection")
    assert len(items) == 1
    assert items[0]["id"] == 1
    
    # Test delete
    deleted = await db_adapter.delete("test_collection", 1)
    assert deleted is True
    
    # Verify item is gone
    items = await db_adapter.list("test_collection")
    assert len(items) == 0
    
    await db_adapter.disconnect()


@pytest.mark.asyncio
async def test_db_adapter_factory():
    # Test getting a registered adapter
    adapter = DatabaseAdapterFactory.get_adapter("mock")
    assert isinstance(adapter, MockDatabaseAdapter)
    
    # Test getting an unregistered adapter
    with pytest.raises(ValueError):
        DatabaseAdapterFactory.get_adapter("nonexistent")
