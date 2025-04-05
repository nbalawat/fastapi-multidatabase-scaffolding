# SQL Server UUID Troubleshooting Guide

## Overview

This document covers common issues and solutions for handling UUIDs with SQL Server in our application. SQL Server uses the `UNIQUEIDENTIFIER` type for UUIDs, which requires special handling compared to other database systems.

## Common Issues

### 1. Type Mismatch Errors

SQL Server requires UUIDs to be properly cast to `UNIQUEIDENTIFIER` when used in queries. Common errors include:

- `Error converting data type nvarchar to uniqueidentifier`
- `Conversion failed when converting from a character string to uniqueidentifier`

### 2. UUID Format Requirements

SQL Server expects UUIDs in the standard format: `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` (e.g., `123e4567-e89b-12d3-a456-426614174000`).

## Solutions Implemented

### 1. Adapter-Level UUID Handling

The SQL Server adapter has been updated to properly handle UUIDs by using the `CAST` function in SQL queries:

```python
# For queries with UUID fields (like 'id')
if field == "id" and isinstance(id_or_key, str):
    query = f"SELECT * FROM {collection} WHERE {field} = CAST(? AS UNIQUEIDENTIFIER)"
```

This ensures that string UUIDs are properly converted to SQL Server's UNIQUEIDENTIFIER type during query execution.

### 2. Schema-Level Configuration

The SQL Server schema defines the `id` field as `UNIQUEIDENTIFIER`:

```python
columns = {
    "id": "UNIQUEIDENTIFIER PRIMARY KEY",
    # other columns...
}
```

### 3. Model Preparation

The `prepare_sqlserver_model` function in `app/utils/sqlserver/schema_utils.py` handles UUID generation and ensures proper formatting:

```python
# Generate ID if not present
if "id" not in db_model:
    db_model["id"] = str(uuid4())
```

## Troubleshooting Steps

If you encounter UUID-related issues with SQL Server:

1. **Check Query Construction**: Ensure that UUID fields are properly cast using `CAST(? AS UNIQUEIDENTIFIER)` in SQL queries.

2. **Verify UUID Format**: Confirm that UUIDs are in the standard format with hyphens.

3. **Inspect Database Schema**: Verify that UUID columns are defined as `UNIQUEIDENTIFIER` in the database schema.

4. **Debug Query Parameters**: Log the actual values being passed to SQL queries to ensure they are valid UUIDs.

## Testing UUID Handling

To test UUID handling, you can use the following approaches:

1. **Create a record with a UUID**: Test the creation of a new record with a UUID field.

```python
import uuid
test_id = str(uuid.uuid4())
data = {"id": test_id, "name": "Test Record"}
result = await db_adapter.create("test_collection", data)
```

2. **Retrieve a record by UUID**: Test retrieving a record using its UUID.

```python
retrieved = await db_adapter.read("test_collection", test_id)
```

3. **Update a record by UUID**: Test updating a record identified by UUID.

```python
update_data = {"name": "Updated Test Record"}
updated = await db_adapter.update("test_collection", test_id, update_data)
```

4. **Delete a record by UUID**: Test deleting a record by its UUID.

```python
deleted = await db_adapter.delete("test_collection", test_id)
```

## Best Practices

1. **Always Use String UUIDs**: In your application code, always use string representations of UUIDs.

2. **Let the Adapter Handle Casting**: The SQL Server adapter will handle the proper casting of UUIDs to UNIQUEIDENTIFIER.

3. **Use UUID Generation Utilities**: Use Python's `uuid` module to generate valid UUIDs.

4. **Validate UUIDs**: When accepting UUIDs from external sources, validate their format before using them in database operations.
