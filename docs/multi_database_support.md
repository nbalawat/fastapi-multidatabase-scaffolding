# Multi-Database Support

This document outlines the architecture and implementation details for supporting multiple active database connections in the FastAPI application, with different endpoints using different databases.

## Overview

The multi-database architecture allows the application to:

1. Connect to multiple databases simultaneously
2. Route specific endpoints to specific databases
3. Maintain backward compatibility with existing code
4. Configure database connections through environment variables
5. Support different database types (PostgreSQL, MongoDB, SQL Server, MySQL)

## Architecture

### Database Configuration

The application will support multiple database configurations through an enhanced settings model:

```python
# In app/core/config.py
from pydantic import BaseModel

class DatabaseConfig(BaseModel):
    db_type: Literal["postgres", "mysql", "sqlserver", "mongodb"]
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    connection_string: Optional[str] = None
    
class Settings(BaseSettings):
    # Existing settings...
    
    # Primary database (for backward compatibility)
    db_type: Literal["postgres", "mysql", "sqlserver", "mongodb"] = "postgres"
    db_host: str = "localhost"
    db_port: int = Field(default=5432)
    db_user: str = "postgres"
    db_password: str = ""
    db_name: str = "fastapi_db"
    
    # Multiple database configurations
    databases: Dict[str, DatabaseConfig] = {}
```

### Database Dependencies

The application will provide specific dependencies for different database connections:

```python
# In app/api/dependencies/db.py
async def get_db_adapter(db_name: Optional[str] = None) -> AsyncGenerator[DatabaseAdapter, None]:
    """Get the database adapter for a specific database or the default one.
    
    Args:
        db_name: The name of the database configuration to use, or None for the primary database
        
    Yields:
        The database adapter
    """
    settings = get_settings()
    
    if db_name and db_name in settings.databases:
        db_config = settings.databases[db_name]
        adapter = DatabaseAdapterFactory.get_adapter(db_config.db_type)
        # Configure adapter with the specific database settings
        adapter.configure(db_config)
    else:
        # Use the primary database configuration
        adapter = DatabaseAdapterFactory.get_adapter(settings.db_type)
    
    await adapter.connect()
    try:
        yield adapter
    finally:
        await adapter.disconnect()

# Create specific dependencies for different databases
def get_user_db():
    """Dependency for the user database."""
    return get_db_adapter("users_db")

def get_product_db():
    """Dependency for the product database."""
    return get_db_adapter("products_db")

def get_analytics_db():
    """Dependency for the analytics database."""
    return get_db_adapter("analytics_db")
```

### Controller Modifications

The base controller will be updated to accept a specific database adapter:

```python
# In app/controllers/base.py
class BaseController:
    def __init__(self, model_name: Optional[str] = None, db_adapter: Optional[DatabaseAdapter] = None):
        self.model_name = model_name or self._get_model_name()
        self.db_adapter = db_adapter
        
    async def _get_db(self):
        """Get the database adapter."""
        if self.db_adapter:
            return self.db_adapter
            
        # Fall back to the default adapter
        from app.api.dependencies.db import get_db_adapter
        return await anext(get_db_adapter())
```

### Router Utilities

The router utilities will be enhanced to support database-specific dependencies:

```python
# In app/utils/router_utils.py
def create_standard_routes(
    router: APIRouter,
    controller_class: Type[BaseController],
    model_class: Type[BaseModel],
    db_dependency: Callable = Depends(get_db_adapter),
    # Other parameters...
):
    """Create standard CRUD routes for a model.
    
    Args:
        router: The router to add the routes to
        controller_class: The controller class to use
        model_class: The model class to use
        db_dependency: The database dependency to use
        # Other parameters...
    """
    # Create a controller instance with the specified database
    controller = controller_class()
    
    @router.post("/", response_model=model_class)
    async def create_item(
        item: model_class,
        db: DatabaseAdapter = db_dependency,
        # Other dependencies...
    ):
        controller.db_adapter = db
        return await controller.create(item.dict())
    
    # Other route definitions...
```

## Usage Examples

### Route Definition

```python
# In app/api/routes/users.py
from app.api.dependencies.db import get_user_db
from app.controllers.users import UserController
from app.models.users import User

router = APIRouter()
create_standard_routes(
    router=router,
    controller_class=UserController,
    model_class=User,
    db_dependency=Depends(get_user_db)
)

# In app/api/routes/products.py
from app.api.dependencies.db import get_product_db
from app.controllers.products import ProductController
from app.models.products import Product

router = APIRouter()
create_standard_routes(
    router=router,
    controller_class=ProductController,
    model_class=Product,
    db_dependency=Depends(get_product_db)
)
```

### Configuration

The application will support configuring multiple databases through environment variables:

```
# Primary database (for backward compatibility)
DB_TYPE=postgres
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=main_db

# User database configuration
DATABASES__users_db__DB_TYPE=mongodb
DATABASES__users_db__DB_HOST=localhost
DATABASES__users_db__DB_PORT=27017
DATABASES__users_db__DB_USER=mongodb_user
DATABASES__users_db__DB_PASSWORD=password
DATABASES__users_db__DB_NAME=users_db

# Product database configuration
DATABASES__products_db__DB_TYPE=sqlserver
DATABASES__products_db__DB_HOST=localhost
DATABASES__products_db__DB_PORT=1433
DATABASES__products_db__DB_USER=sa
DATABASES__products_db__DB_PASSWORD=YourStrong@Passw0rd
DATABASES__products_db__DB_NAME=products_db
```

## Implementation Steps

1. Update the `Settings` class to support multiple database configurations
2. Enhance the `DatabaseAdapter` interface with a `configure` method
3. Update the database dependencies to support specific database connections
4. Modify the `BaseController` to accept and use specific database adapters
5. Update the router utilities to support database-specific dependencies
6. Create database-specific dependencies for different models
7. Update documentation and tests

## Benefits

1. **Backward Compatibility**: Existing code continues to work with the primary database
2. **Flexibility**: Different endpoints can use different databases
3. **Separation of Concerns**: Each model can be associated with its most appropriate database
4. **Scalability**: You can add new database connections without changing existing code
5. **Type Safety**: Maintains type safety throughout the codebase
6. **DRY Principles**: Reuses existing code patterns and avoids duplication

## Considerations

1. **Connection Pooling**: Consider implementing connection pooling for better performance
2. **Transaction Management**: Be aware of transaction boundaries across different databases
3. **Schema Management**: Ensure schema migrations are applied to the correct databases
4. **Testing**: Update tests to use the correct database connections

## Future Enhancements

1. **Dynamic Database Selection**: Allow dynamic selection of databases based on request parameters
2. **Read/Write Splitting**: Support read replicas for read-heavy operations
3. **Sharding**: Implement database sharding for horizontal scaling
4. **Cross-Database Queries**: Support queries that span multiple databases
