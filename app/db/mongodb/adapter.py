from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from bson.errors import InvalidId

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import Settings
from app.db.base import DatabaseAdapter, DatabaseAdapterFactory


class MongoDBAdapter(DatabaseAdapter):
    """MongoDB database adapter implementation.
    
    This adapter uses Motor for async MongoDB operations.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the MongoDB adapter.
        
        Args:
            settings: Application settings containing database configuration
        """
        self.settings = settings
        self._client: Optional[AsyncIOMotorClient] = None
        self._db_name = settings.db_name
    
    async def connect(self) -> None:
        """Connect to the MongoDB database."""
        if self._client is None:
            # Use the provided connection string if available, otherwise construct one
            if self.settings.mongodb_connection_string:
                connection_string = self.settings.mongodb_connection_string
            else:
                # Construct the MongoDB connection string
                connection_string = (
                    f"mongodb://{self.settings.db_user}:{self.settings.db_password}"
                    f"@{self.settings.db_host}:{self.settings.db_port}/{self._db_name}"
                )
            
            # Create a client
            self._client = AsyncIOMotorClient(connection_string)
    
    async def disconnect(self) -> None:
        """Disconnect from the MongoDB database."""
        if self._client is not None:
            self._client.close()
            self._client = None
    
    def _get_db(self):
        """Get the database instance.
        
        Returns:
            The database instance
        """
        if self._client is None:
            raise RuntimeError("Not connected to MongoDB")
        return self._client[self._db_name]
    
    def _get_collection(self, collection: str):
        """Get a collection.
        
        Args:
            collection: The name of the collection
            
        Returns:
            The collection instance
        """
        return self._get_db()[collection]
    
    def _convert_id(self, id: Any) -> Union[ObjectId, str]:
        """Convert a string ID to an ObjectId if possible.
        
        Args:
            id: The ID to convert
            
        Returns:
            An ObjectId if the ID is a valid ObjectId string, otherwise the original ID
        """
        if isinstance(id, str):
            try:
                return ObjectId(id)
            except InvalidId:
                # If it's not a valid ObjectId, it might be a username or other identifier
                return id
        return id
    
    def _prepare_document_filter(self, id: Any) -> Dict[str, Any]:
        """Prepare a filter for finding a document by ID.
        
        This tries to convert the ID to an ObjectId if possible, and falls back to
        username lookup if it's not a valid ObjectId.
        
        Args:
            id: The ID to use in the filter
            
        Returns:
            A filter dictionary
        """
        try:
            return {"_id": ObjectId(id)}
        except (InvalidId, TypeError):
            # If it's not a valid ObjectId, try username
            return {"username": id}
    
    def _process_document(self, document: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Process a document from MongoDB to make it compatible with the API.
        
        This converts the _id field to a string id field.
        
        Args:
            document: The document to process
            
        Returns:
            The processed document, or None if the input was None
        """
        if document is None:
            return None
        
        # Create a copy of the document
        result = dict(document)
        
        # Convert _id to string id
        if "_id" in result:
            result["id"] = str(result.pop("_id"))
        
        return result
    
    async def create(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document in the specified collection.
        
        Args:
            collection: The name of the collection
            data: The data to insert
            
        Returns:
            The created document with any generated fields (like ID)
        """
        if self._client is None:
            await self.connect()
        
        # Get the collection
        coll = self._get_collection(collection)
        
        # Insert the document
        result = await coll.insert_one(data)
        
        # Get the inserted document
        document = await coll.find_one({"_id": result.inserted_id})
        
        # Process and return the document
        return self._process_document(document)
    
    async def read(self, collection: str, id: Any) -> Optional[Dict[str, Any]]:
        """Read a document by its ID.
        
        Args:
            collection: The name of the collection
            id: The ID of the document to retrieve
            
        Returns:
            The document if found, None otherwise
        """
        if self._client is None:
            await self.connect()
        
        # Get the collection
        coll = self._get_collection(collection)
        
        # Prepare the filter
        filter_dict = self._prepare_document_filter(id)
        
        # Find the document
        document = await coll.find_one(filter_dict)
        
        # Process and return the document
        return self._process_document(document)
    
    async def update(self, collection: str, id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a document by its ID.
        
        Args:
            collection: The name of the collection
            id: The ID of the document to update
            data: The data to update
            
        Returns:
            The updated document if found, None otherwise
        """
        if self._client is None:
            await self.connect()
        
        # Get the collection
        coll = self._get_collection(collection)
        
        # Prepare the filter
        filter_dict = self._prepare_document_filter(id)
        
        # Update the document
        document = await coll.find_one_and_update(
            filter_dict,
            {"$set": data},
            return_document=True
        )
        
        # Process and return the document
        return self._process_document(document)
    
    async def delete(self, collection: str, id: Any) -> bool:
        """Delete a document by its ID.
        
        Args:
            collection: The name of the collection
            id: The ID of the document to delete
            
        Returns:
            True if the document was deleted, False otherwise
        """
        if self._client is None:
            await self.connect()
        
        # Get the collection
        coll = self._get_collection(collection)
        
        # Prepare the filter
        filter_dict = self._prepare_document_filter(id)
        
        # Delete the document
        result = await coll.delete_one(filter_dict)
        
        # Return True if a document was deleted
        return result.deleted_count > 0
    
    async def list(self, collection: str, skip: int = 0, limit: int = 100, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List documents from a collection with pagination and optional filtering.
        
        Args:
            collection: The name of the collection
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            query: Optional dictionary of field-value pairs to filter by
            
        Returns:
            A list of documents
        """
        if self._client is None:
            await self.connect()
        
        # Get the collection
        coll = self._get_collection(collection)
        
        # Prepare the filter
        filter_dict = query or {}
        
        # Find documents with pagination and filtering
        cursor = coll.find(filter_dict).skip(skip).limit(limit)
        
        # Get the documents
        documents = await cursor.to_list(length=limit)
        
        # Process and return the documents
        return [self._process_document(doc) for doc in documents]


# Register the MongoDB adapter with the factory
DatabaseAdapterFactory.register("mongodb", MongoDBAdapter)
