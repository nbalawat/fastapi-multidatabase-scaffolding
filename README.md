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
├── models/       # Domain models
├── schemas/      # Pydantic schemas for request/response validation
└── services/     # Business logic and services
```

## Development

This project uses `uv` for dependency management and follows test-driven development practices.

### Setup

1. Clone the repository
2. Install dependencies with `uv sync`
3. Configure environment variables
4. Run the development server

### Testing

Run tests with pytest:

```bash
pytest
```

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
