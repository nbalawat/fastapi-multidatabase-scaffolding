# Database Integration Guide

This document explains how the model-centric architecture integrates with multiple database backends.

## Overview

The application uses a layered approach to database integration:

1. **Pydantic Models**: Define the data structure and validation rules
2. **Database Schemas**: Map Pydantic models to database-specific schemas
3. **Controllers**: Handle business logic and database operations
4. **Database Adapters**: Provide database-specific CRUD operations

This approach ensures:
- Type safety across the application
- Seamless switching between database backends
- Consistent validation and error handling
- Automatic schema creation and management

## Database Schema Registry

The Schema Registry is the central component that manages database schemas:

```python
from app.db.schema_registry import get_schema_registry

# Get the schema registry
schema_registry = get_schema_registry()

# Check if a schema exists for a model and database type
has_schema = schema_registry.has_schema("notes", "postgres")

# Get a schema for a model and database type
notes_schema = schema_registry.get_schema("notes", "postgres")

# Get all schemas for a model
notes_schemas = schema_registry.get_schemas_for_model("notes")
```

## Database Schema Implementation

Each model has database-specific schema implementations:

```python
# PostgreSQL schema for notes
class NotesPostgresSchema(BaseSchema[NoteInDB]):
    def get_table_name(self) -> str:
        return "notes"
    
    def get_create_table_statement(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS notes (
            id UUID PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            content TEXT,
            tags TEXT[],
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );
        """
    
    def to_db_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # PostgreSQL specific conversions
        db_model = data.copy()
        
        # Ensure tags is a list for PostgreSQL array
        if "tags" in db_model and db_model["tags"] is None:
            db_model["tags"] = []
            
        return db_model
    
    def from_db_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # PostgreSQL specific conversions
        api_model = data.copy()
        
        # Handle PostgreSQL array format for tags
        if "tags" in api_model and isinstance(api_model["tags"], str):
            from app.utils.postgres.array_parser import parse_postgres_array
            api_model["tags"] = parse_postgres_array(api_model["tags"], "tags")
            
        return api_model
```


## Automatic Database Initialization

The application automatically initializes database schemas on startup:

1. The Schema Registry discovers all schema implementations
2. The Database Initializer creates tables/collections for each schema
3. Controllers use the schemas for data conversion and validation

This process ensures that:
- Database tables/collections are created if they don't exist
- Schema changes are applied consistently across database types
- New models are automatically supported without manual schema creation

### Admin User Initialization

The application also initializes admin users during startup. This is handled by the `AdminInitializer` class, which uses the Schema Registry to get the appropriate schema for the users model. The admin user is created if it doesn't already exist, ensuring that there's always an admin user available for the application.

```python
from app.db.admin_initializer import AdminInitializer

# Initialize admin users for all configured database types
admin_initializer = AdminInitializer()
await admin_initializer.initialize_admin_users()

# Or for a specific database type
await admin_initializer.initialize_admin_user("postgres")
```

## Traceability and Validation

### Model-Database Traceability

The system provides traceability between models and database implementations:

1. **Schema Registry**: Maintains a mapping between models and database schemas
2. **Controller Integration**: Controllers automatically use the appropriate schema
3. **Validation Hooks**: Pre/post processing hooks for custom validation logic

### Database Implementation Validation

To validate if a model has a database implementation:

```python
# Check if a model has a database implementation
schema_registry = get_schema_registry()
has_postgres_impl = schema_registry.has_schema("notes", "postgres")
has_mongodb_impl = schema_registry.has_schema("notes", "mongodb")

# Get all supported database types for a model
notes_schemas = schema_registry.get_schemas_for_model("notes")
supported_db_types = list(notes_schemas.keys())
```

## Adding a New Model

To add a new model with database support, follow these steps:

1. Create a Pydantic model in `app/models/<model_name>/model.py`
2. Create database schemas for each supported database type:
   - `app/db/schemas/<model_name>/postgres.py`
   - `app/db/schemas/<model_name>/mongodb.py`
   - `app/db/schemas/<model_name>/sqlserver.py`
3. Create a controller in `app/models/<model_name>/controller.py` that extends `BaseController`
4. Create a router in `app/models/<model_name>/router.py` that uses the controller

The Schema Registry will automatically discover and register the new schemas on application startup.

## Testing Database Integration

The application includes tests to verify database integration:

1. **Schema Discovery Tests**: Verify that schemas are correctly discovered
2. **Schema Validation Tests**: Verify that schemas correctly validate data
3. **Database Initialization Tests**: Verify that tables/collections are created
4. **CRUD Operation Tests**: Verify that CRUD operations work correctly

These tests ensure that the database integration is working correctly and that all models have the necessary database implementations.
