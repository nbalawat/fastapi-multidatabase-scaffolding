from typing import Any, Dict, List, Optional

from sqlalchemy import delete, insert, select, update, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.base import DatabaseAdapter, DatabaseAdapterFactory
from app.db.mysql.session import create_async_session


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter implementation.
    
    This adapter uses SQLAlchemy Core for database operations.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the MySQL adapter.
        
        Args:
            settings: Application settings containing database configuration
        """
        self.settings = settings
        self._session: Optional[AsyncSession] = None
    
    async def connect(self) -> None:
        """Connect to the MySQL database."""
        if self._session is None:
            self._session = create_async_session(self.settings)
    
    async def disconnect(self) -> None:
        """Disconnect from the MySQL database."""
        if self._session is not None:
            await self._session.close()
            self._session = None
    
    async def create(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the specified table.
        
        Args:
            collection: The name of the table
            data: The data to insert
            
        Returns:
            The created record with any generated fields (like ID)
        """
        if self._session is None:
            await self.connect()
        
        # Create an insert statement
        stmt = insert(text(collection)).values(**data).returning(text("*"))
        
        # Execute the statement
        result = await self._session.execute(stmt)
        await self._session.commit()
        
        # Return the created record
        return dict(result.scalar_one())
    
    async def read(self, collection: str, id: Any) -> Optional[Dict[str, Any]]:
        """Read a record by its ID.
        
        Args:
            collection: The name of the table
            id: The ID of the record to retrieve
            
        Returns:
            The record if found, None otherwise
        """
        if self._session is None:
            await self.connect()
        
        # Create a select statement
        stmt = select(text("*")).select_from(text(collection)).where(text("id = :id")).params(id=id)
        
        # Execute the statement
        result = await self._session.execute(stmt)
        
        # Return the record if found
        record = result.scalar_one_or_none()
        return dict(record) if record else None
    
    async def update(self, collection: str, id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by its ID.
        
        Args:
            collection: The name of the table
            id: The ID of the record to update
            data: The data to update
            
        Returns:
            The updated record if found, None otherwise
        """
        if self._session is None:
            await self.connect()
        
        # Create an update statement
        stmt = (
            update(text(collection))
            .where(text("id = :id"))
            .values(**data)
            .returning(text("*"))
            .params(id=id)
        )
        
        # Execute the statement
        result = await self._session.execute(stmt)
        await self._session.commit()
        
        # Return the updated record if found
        record = result.scalar_one_or_none()
        return dict(record) if record else None
    
    async def delete(self, collection: str, id: Any) -> bool:
        """Delete a record by its ID.
        
        Args:
            collection: The name of the table
            id: The ID of the record to delete
            
        Returns:
            True if the record was deleted, False otherwise
        """
        if self._session is None:
            await self.connect()
        
        # Create a delete statement
        stmt = delete(text(collection)).where(text("id = :id")).params(id=id)
        
        # Execute the statement
        result = await self._session.execute(stmt)
        await self._session.commit()
        
        # Return True if a record was deleted
        return result.rowcount > 0
    
    async def list(self, collection: str, skip: int = 0, limit: int = 100, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List records from a table with pagination and optional filtering.
        
        Args:
            collection: The name of the table
            skip: Number of records to skip
            limit: Maximum number of records to return
            query: Optional dictionary of field-value pairs to filter by
            
        Returns:
            A list of records
        """
        if self._session is None:
            await self.connect()
        
        # Create a select statement with pagination
        stmt = (
            select(text("*"))
            .select_from(text(collection))
        )
        
        # Add where clauses for each query parameter
        if query:
            for field, value in query.items():
                stmt = stmt.where(text(f"{field} = :{field}")).params(**{field: value})
        
        # Add pagination
        stmt = stmt.offset(skip).limit(limit)
        
        # Execute the statement
        result = await self._session.execute(stmt)
        
        # Return the records
        return [dict(record) for record in result.scalars().all()]


# Register the MySQL adapter with the factory
DatabaseAdapterFactory.register("mysql", MySQLAdapter)
