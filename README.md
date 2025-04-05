# FastAPI Scaffolding with Multiple Database Support

A configurable FastAPI server that supports multiple database ecosystems (PostgreSQL, MySQL, SQL Server, MongoDB) with features for authentication, authorization, rate limiting, error logging, and async job processing.

## Features

- **Multiple Database Support**: Connect to PostgreSQL, MySQL, SQL Server, or MongoDB
- **Configuration-Driven**: Easily configure the application through environment variables
- **Authentication & Authorization**: Secure API endpoints with JWT authentication and role-based access control
- **Route Guards**: Protect routes based on user roles and permissions
- **Microservice Communication**: Interact with other microservices
- **Rate Limiting**: Prevent abuse of your API
- **Error Logging**: Comprehensive logging for debugging and monitoring
- **Async Job Processing**: Handle long-running tasks asynchronously

## Project Structure

The project follows a modular structure with clear separation of concerns:

```
app/
├── core/         # Core functionality (config, security, logging)
├── api/          # API routes and dependencies
├── db/           # Database adapters for different database systems
├── models/       # Domain models organized by feature
│   ├── notes/    # Notes feature (model, controller, router)
│   └── users/    # Users feature (model, controller, router)
├── utils/        # Utility functions
│   ├── generic/  # Database-agnostic utilities
│   ├── postgres/ # PostgreSQL-specific utilities
│   ├── sqlserver/ # SQL Server-specific utilities
│   └── mongo/    # MongoDB-specific utilities
├── schemas/      # Pydantic schemas for request/response validation
└── services/     # Business logic and services
```

## Model-Centric Architecture

This project implements a model-centric architecture that separates model-specific logic from database-specific code:

### Key Components

1. **Base Controller**: A generic controller that provides CRUD operations for any model
   ```python
   class NotesController(BaseController[NoteCreate, NoteUpdate, Note]):
       # Override base methods for model-specific logic
       def _preprocess_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
           # Ensure tags is a list
           if "tags" not in data or data["tags"] is None:
               data["tags"] = []
           return data
   ```

2. **Database-Specific Utilities**: Handle serialization/deserialization for each database type
   ```python
   # PostgreSQL array parser
   def parse_postgres_array(value: Any, field_name: str = "unknown") -> List[Any]:
       # Implementation for parsing PostgreSQL arrays
   ```

3. **Model-Specific Controllers**: Extend the base controller with model-specific logic
   ```python
   # Add custom methods to your controller
   async def search_content(self, query: str) -> List[Dict[str, Any]]:
       # Custom search implementation
       all_notes = await self.list(0, 1000)
       return [note for note in all_notes 
               if query.lower() in note.get("content", "").lower()]
   ```

### Benefits

- **Separation of Concerns**: Model logic is separate from database-specific code
- **DRY Code**: Common functionality is extracted to reusable components
- **Consistent Interfaces**: All models follow the same patterns
- **Type Safety**: Proper type annotations throughout the codebase

For more details, see the [architecture documentation](docs/architecture.md).

## Development

This project uses `uv` for dependency management and follows test-driven development practices.

### Setup

1. Clone the repository
2. Install dependencies with `uv sync`
3. Configure environment variables
4. Run the development server

### Testing

This project uses pytest for testing. You can run tests for all database types or target specific database implementations.

#### Running All Tests

To run all tests:

```bash
python -m pytest
```

#### Database-Specific Tests

To run tests for a specific database type:

##### PostgreSQL Tests

```bash
python -m pytest app/scripts/tests/test_crud_postgres.py
python -m pytest app/scripts/tests/test_api_postgres.py
python -m pytest app/scripts/tests/test_rbac_postgres.py
```

##### MongoDB Tests

```bash
python -m pytest app/scripts/tests/test_crud_mongodb.py
python -m pytest app/scripts/tests/test_api_mongodb.py
python -m pytest app/scripts/tests/test_rbac_mongodb.py
```

##### SQL Server Tests

```bash
python -m pytest app/scripts/tests/test_crud_sqlserver.py
python -m pytest app/scripts/tests/test_api_sqlserver.py
python -m pytest app/scripts/tests/test_rbac_sqlserver.py
```

#### Running Specific Test Functions

To run a specific test function:

```bash
python -m pytest app/scripts/tests/test_crud_sqlserver.py::test_create_note
```

#### Test Requirements

Before running tests, ensure that:

1. The appropriate database servers are running and accessible
2. Database initialization scripts have been run
3. The environment variables are correctly set for the target database

You can use the Docker setup to ensure all required services are available.

## Docker

Docker configuration is available in the `docker` directory, which includes Jupyter Lab for interactive development.

## Role-Based Access Control (RBAC)

This application implements a comprehensive role-based access control system that allows fine-grained permission management.

### Roles and Permissions

The system comes with several default roles:

- **Admin**: Full access to all features
- **Editor**: Can create, read, update, and delete content
- **User**: Standard user with basic content management permissions
- **Guest**: Limited to read-only access

Each role has a set of permissions that determine what actions users with that role can perform.

### Testing RBAC

You can test the RBAC system programmatically using the provided test script:

```bash
python -m app.scripts.test_rbac
```

This script will:
1. Login as admin
2. Test role management endpoints
3. Create test users with different roles
4. Test permission-based access to endpoints

### Using Swagger UI for Authentication

1. Navigate to the Swagger UI at `http://localhost:8000/docs`
2. Click on the "Authorize" button at the top right
3. You'll see two authorization options:
   - **OAuth2PasswordBearer**: Use this for direct login. Enter your username and password.
   - **bearerAuth**: Use this if you already have a token. Enter your token in the format `Bearer YOUR_TOKEN` (replace YOUR_TOKEN with the actual token)
4. Click "Authorize" and close the dialog
5. You can now access protected endpoints

**Note**: If the authorization dialog appears empty or doesn't show these options, try refreshing the page or restarting the application.

### Using RBAC with Swagger UI

To interact with the RBAC system through Swagger UI:

1. **Access the Swagger UI**:
   - Ensure your FastAPI application is running
   - Navigate to `http://localhost:8000/docs` in your browser

## UUID Handling

The application includes robust UUID handling throughout the authentication and data processing pipeline:

- **Automatic UUID Conversion**: The system automatically converts UUID objects to strings in API responses to ensure compatibility with JSON serialization and client applications.
- **Flexible ID Fields**: Models support both string and UUID types for ID fields, allowing flexibility in how IDs are stored and processed.
- **User Authentication**: When creating resources that require user association (like notes), the user ID is automatically extracted from the authentication token and properly formatted.

### Example: Creating Notes with Authenticated User

When creating a note while authenticated, you don't need to specify the user ID - it's automatically set from your authentication token:

```python
# NotesController.create_with_user method handles this automatically
async def create_with_user(self, data: NoteCreate, user: User) -> Dict[str, Any]:
    data_dict = data.model_dump() if hasattr(data, "model_dump") else data.dict()
    # Set the user_id from the authenticated user
    data_dict["user_id"] = str(user.id) if hasattr(user.id, 'hex') else user.id
    return await self.create(data_dict)
```

2. **Authenticate as Admin**:
   - Click on the `/api/v1/token` endpoint (POST)
   - Click "Try it out"
   - Enter admin credentials:
     ```
     username: admin
     password: admin123
     ```
   - Execute and copy the access token from the response

3. **Authorize Swagger**:
   - Click the "Authorize" button at the top right of the Swagger UI
   - Enter `Bearer {your_token}` in the value field (replace {your_token} with the token you copied)
   - Click "Authorize" and then "Close"

4. **Create a Custom Role**:
   - Navigate to the `/api/v1/roles` endpoint (POST)
   - Click "Try it out"
   - Enter the role data in the request body:
     ```json
     {
       "name": "content_reviewer",
       "description": "Can review and comment on content",
       "permissions": [
         "note:create",
         "note:read",
         "note:update"
       ]
     }
     ```
   - Execute the request

5. **List All Roles**:
   - Navigate to the `/api/v1/roles` endpoint (GET)
   - Click "Try it out"
   - Execute the request to see all roles including your new one

6. **Get Role Details**:
   - Navigate to the `/api/v1/roles/{role_name}` endpoint (GET)
   - Click "Try it out"
   - Enter "content_reviewer" in the role_name field
   - Execute the request

### Troubleshooting RBAC

If you encounter issues with the RBAC system:

1. **Authentication Errors** (`"detail": "Not authenticated"`): 
   - This error occurs when you haven't properly authenticated or your token has expired
   - Make sure you've obtained a valid token from the `/api/v1/token` endpoint
   - Ensure you're including the token in the Authorization header with the format `Bearer {token}`
   - In Swagger UI, verify you've clicked the "Authorize" button and entered the token correctly
   - Check that your token hasn't expired (tokens typically expire after a certain period)
   - **Important**: When using Swagger UI, make sure to use the full token value without any quotes
   - When making direct API calls with curl or httpx, use: `curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/users/`
   - If you're still having issues, try restarting the application after making changes to the authentication system

2. **Permission Errors** (`"detail": "Not enough permissions"`): 
   - This occurs when your user doesn't have the required role or permissions
   - Verify that the user has the correct role assigned
   - Check that the role has the necessary permissions for the action

3. **Database Connection Issues**:
   - Check that your database connection is working properly
   - Verify that the database adapter is correctly configured
   - Examine the logs for connection errors

4. **Other Common Issues**:
   - Examine the application logs for detailed error messages
   - Ensure that the role middleware is correctly configured
   - Verify that the permissions are correctly defined in the system
