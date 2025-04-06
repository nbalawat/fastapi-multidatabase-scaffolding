# SQL Server Integration Issues and Solutions

This document summarizes all the SQL Server integration issues encountered during the development of the FastAPI multiple database scaffolding project. It serves as a reference for future development efforts.

## Connection and Configuration Issues

### 1. ODBC Driver Configuration

**Issue**: The SQL Server container failed to connect due to ODBC driver configuration problems.

**Solution**: 
- Updated `setup-odbc.sh` to dynamically find the installed Microsoft ODBC driver
- Added proper error handling and logging for ODBC connection failures
- Ensured the correct ODBC driver version is installed in the Docker container

```bash
# Dynamic ODBC driver detection in setup-odbc.sh
ODBC_DRIVER=$(odbcinst -q -d | grep -i "ODBC Driver" | head -n 1 | tr -d "[]")
if [ -z "$ODBC_DRIVER" ]; then
    echo "Error: No Microsoft ODBC driver found"
    exit 1
fi
```

### 2. Connection String Format

**Issue**: Inconsistent connection string formats caused connection failures.

**Solution**:
- Standardized connection string format for SQL Server
- Added proper error handling for connection failures
- Added detailed logging for connection attempts

```python
# Standardized connection string format
conn_str = f"DRIVER={{{driver}}};SERVER={host},{port};DATABASE={database};UID={username};PWD={password}"
```

## UUID Handling

### 1. UUID Type Mismatch

**Issue**: SQL Server requires UUIDs to be cast to UNIQUEIDENTIFIER, causing type mismatch errors.

**Solution**:
- Added special handling in the SQL Server adapter for UUID fields
- Used `CAST(? AS UNIQUEIDENTIFIER)` in SQL queries for UUID fields
- Standardized UUID handling across all CRUD operations

```python
# Special handling for UUID fields in SQL Server
if field == "id" and isinstance(id_or_key, str):
    query = f"SELECT * FROM {collection} WHERE {field} = CAST(? AS UNIQUEIDENTIFIER)"
```

### 2. UUID Format Requirements

**Issue**: SQL Server expects UUIDs in the standard format with hyphens.

**Solution**:
- Ensured all UUIDs are properly formatted with hyphens
- Added validation for UUID formats
- Implemented automatic UUID conversion in the BaseController

## JSON Data Handling

### 1. JSON String Parsing

**Issue**: SQL Server stores JSON data as strings, requiring explicit parsing.

**Solution**:
- Created a `parse_json_string` helper function to handle various edge cases
- Implemented proper JSON parsing for all CRUD operations
- Added error handling for malformed JSON

```python
# JSON parsing helper function
def parse_json_string(json_str):
    """Parse a JSON string, handling various edge cases."""
    if not json_str:
        return []
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Fallback parsing for malformed JSON
        logger.warning(f"Failed to parse JSON string: {json_str}")
        return []
```

### 2. Tags Field Handling

**Issue**: The tags field was inconsistently handled across different database adapters.

**Solution**:
- Standardized tags field handling in the SQL Server adapter
- Ensured tags are always returned as lists
- Added proper serialization/deserialization for tags

## Cursor Handling

**Issue**: The SQLServerAdapter's cursor method was incorrectly implemented, causing errors in async with statements.

**Solution**:
- Fixed the cursor method to return the connection's cursor method directly (not awaited)
- Updated all CRUD operations to use the cursor correctly
- Added proper error handling for cursor operations

```python
async def cursor(self):
    """Get a cursor for the SQL Server connection."""
    if self._client is None:
        await self.connect()
    return self._client.cursor()  # Return directly, not awaited
```

## Role and Permission Handling

### 1. Role Creation Issues

**Issue**: Creating roles in SQL Server resulted in 500 errors due to incorrect ID handling.

**Solution**:
- Added special handling for roles in the SQL Server adapter
- Updated the create method to use the role name as the ID
- Updated the read method to query by both name and ID for roles

```python
# Special handling for roles in SQL Server adapter
if collection == "roles":
    # Use role name as ID for roles
    if "name" in data and not data.get("id"):
        data["id"] = data["name"]
```

### 2. Permission Serialization

**Issue**: Permissions were not properly serialized/deserialized in SQL Server.

**Solution**:
- Improved JSON serialization/deserialization for permissions
- Added proper error handling with detailed logging
- Updated the role middleware to protect editor-specific paths

## Database Initialization

### 1. Multiple Database Initialization

**Issue**: The application tried to initialize all configured databases instead of only the primary database type.

**Solution**:
- Fixed database initialization to only initialize the primary database type specified in settings
- Prevented the PostgreSQL container from trying to connect to SQL Server
- Added proper error handling for database initialization failures

### 2. Duplicate Parameter Issues

**Issue**: Duplicate `is_active` parameter in admin_initializer.py caused errors.

**Solution**:
- Fixed the issue by excluding `is_active` from the dictionary unpacking
- Added validation for duplicate parameters
- Improved error handling for parameter validation

```python
# Fixed duplicate parameter issue
user_data = {
    "email": admin_email,
    "username": admin_username,
    "password": admin_password,
    # is_active excluded from dictionary unpacking
}
```

## Testing Issues

### 1. RBAC Test Failures

**Issue**: RBAC tests failed due to inconsistent login endpoints.

**Solution**:
- Updated all RBAC test scripts with a more resilient login approach
- Made the login function try multiple possible login endpoints
- Added detailed logging of login attempts
- Implemented proper error handling with try/except blocks

```python
# Resilient login approach
def login(base_url, username, password):
    """Try multiple possible login endpoints."""
    possible_endpoints = [
        "/api/v1/auth/login",
        "/api/v1/login",
        "/auth/login",
        "/api/v1/auth/token"
    ]
    
    for endpoint in possible_endpoints:
        try:
            response = requests.post(
                f"{base_url}{endpoint}",
                json={"username": username, "password": password}
            )
            if response.status_code == 200 and "access_token" in response.json():
                return response.json()["access_token"]
        except Exception as e:
            logger.warning(f"Login attempt failed for {endpoint}: {e}")
    
    raise Exception("Failed to login with any endpoint")
```

### 2. Test Script Port Configuration

**Issue**: Test scripts used hardcoded ports, causing failures in multi-database setup.

**Solution**:
- Updated all test scripts to use the correct ports for each database type
- Made port configuration more flexible
- Added proper error handling for connection failures

## Best Practices for SQL Server Integration

1. **UUID Handling**:
   - Always use string UUIDs in application code
   - Let the SQL Server adapter handle the proper casting to UNIQUEIDENTIFIER
   - Validate UUID formats before database operations

2. **JSON Data**:
   - Always use proper JSON serialization/deserialization
   - Handle edge cases for malformed JSON
   - Use the `parse_json_string` helper function for consistent handling

3. **Connection Management**:
   - Use connection pooling for better performance
   - Properly close connections to avoid resource leaks
   - Add detailed logging for connection issues

4. **Error Handling**:
   - Add specific error handling for SQL Server-specific errors
   - Log detailed error information for debugging
   - Implement retry logic for transient connection issues

5. **Testing**:
   - Create SQL Server-specific tests
   - Test all CRUD operations with various data types
   - Validate UUID handling in tests

6. **Schema Management**:
   - Define SQL Server schemas with proper types
   - Use UNIQUEIDENTIFIER for UUID fields
   - Follow SQL Server naming conventions

## Future Considerations

1. **Connection Pooling**: Implement proper connection pooling for SQL Server to improve performance.

2. **Prepared Statements**: Use prepared statements consistently to improve security and performance.

3. **Transactions**: Implement proper transaction handling for SQL Server operations.

4. **Monitoring**: Add monitoring for SQL Server connection health and performance.

5. **Migrations**: Implement proper database migration tools for SQL Server schema changes.

By following these guidelines and learning from past issues, future development efforts with SQL Server integration should be more efficient and less error-prone.
