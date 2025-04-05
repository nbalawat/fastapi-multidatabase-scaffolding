"""Enhanced OpenAPI documentation for the FastAPI application."""
from typing import Dict, Any, List

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.models.notes import NoteVisibility
from app.models.users import Role


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generate custom OpenAPI schema with enhanced documentation.
    
    Args:
        app: The FastAPI application
        
    Returns:
        The enhanced OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom documentation
    add_custom_documentation(openapi_schema)
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token in the format: Bearer {token}",
        },
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/token",
                    "scopes": {}
                }
            },
            "description": "OAuth2 password flow for authentication"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"bearerAuth": []}, {"OAuth2PasswordBearer": []}]
    
    # Store the schema
    app.openapi_schema = openapi_schema
    
    return app.openapi_schema


def add_custom_documentation(schema: Dict[str, Any]) -> None:
    """Add custom documentation to the OpenAPI schema.
    
    Args:
        schema: The OpenAPI schema
    """
    # Add database information
    schema["info"]["description"] = (
        "# FastAPI Multiple Databases\n\n"
        "This API supports multiple database backends including PostgreSQL, MySQL, and MongoDB.\n\n"
        "## Database Types\n\n"
        "- **PostgreSQL**: Traditional relational database\n"
        "- **MongoDB**: NoSQL document database\n\n"
        "The database type can be configured using the `DB_TYPE` environment variable.\n\n"
        "## Authentication\n\n"
        "This API uses JWT tokens for authentication. To authenticate, use the `/api/v1/token` endpoint.\n\n"
        "## Role-Based Access Control\n\n"
        "The API implements a comprehensive role-based access control system with the following features:\n\n"
        "### Built-in Roles\n\n"
        f"- **{Role.ADMIN.value}**: Full access to all endpoints and features\n"
        f"- **{Role.USER.value}**: Access to user-specific endpoints and content management\n"
        f"- **{Role.GUEST.value}**: Limited access to public endpoints and read-only operations\n\n"
        "### Custom Roles\n\n"
        "Administrators can create custom roles with specific permissions using the `/api/v1/roles` endpoints.\n\n"
        "### Granular Permissions\n\n"
        "The system uses granular permissions for fine-grained access control:\n\n"
        "- **User Management**: user:create, user:read, user:update, user:delete\n"
        "- **Note Management**: note:create, note:read, note:update, note:delete\n"
        "- **Admin Operations**: admin:access, role:manage\n\n"
        "### Permission-Based Access\n\n"
        "API endpoints are protected based on specific permissions rather than just roles, allowing for more flexible access control.\n\n"
    )
    
    # Add examples for notes endpoints
    add_notes_examples(schema)


def add_notes_examples(schema: Dict[str, Any]) -> None:
    """Add examples for notes endpoints to the OpenAPI schema.
    
    Args:
        schema: The OpenAPI schema
    """
    # Example note
    example_note = {
        "title": "Example Note",
        "content": "This is an example note content.",
        "visibility": NoteVisibility.PRIVATE.value,
        "tags": ["example", "documentation"]
    }
    
    # Example note response
    example_note_response = {
        "id": "60d5ec9af682dbd12a0a9fb9",
        "title": "Example Note",
        "content": "This is an example note content.",
        "visibility": NoteVisibility.PRIVATE.value,
        "tags": ["example", "documentation"],
        "user_id": "1",
        "created_at": "2023-04-04T12:00:00",
        "updated_at": None
    }
    
    # Example note update
    example_note_update = {
        "title": "Updated Example Note",
        "content": "This note has been updated."
    }
    
    # Add examples to paths if they exist
    paths = schema.get("paths", {})
    
    # POST /notes
    if "/api/v1/notes" in paths and "post" in paths["/api/v1/notes"]:
        paths["/api/v1/notes"]["post"]["requestBody"]["content"]["application/json"]["example"] = example_note
        paths["/api/v1/notes"]["post"]["responses"]["201"]["content"]["application/json"]["example"] = example_note_response
    
    # GET /notes/{note_id}
    if "/api/v1/notes/{note_id}" in paths and "get" in paths["/api/v1/notes/{note_id}"]:
        paths["/api/v1/notes/{note_id}"]["get"]["responses"]["200"]["content"]["application/json"]["example"] = example_note_response
    
    # PUT /notes/{note_id}
    if "/api/v1/notes/{note_id}" in paths and "put" in paths["/api/v1/notes/{note_id}"]:
        paths["/api/v1/notes/{note_id}"]["put"]["requestBody"]["content"]["application/json"]["example"] = example_note_update
        paths["/api/v1/notes/{note_id}"]["put"]["responses"]["200"]["content"]["application/json"]["example"] = {
            **example_note_response,
            "title": "Updated Example Note",
            "content": "This note has been updated.",
            "updated_at": "2023-04-04T12:30:00"
        }
    
    # GET /notes
    if "/api/v1/notes" in paths and "get" in paths["/api/v1/notes"]:
        paths["/api/v1/notes"]["get"]["responses"]["200"]["content"]["application/json"]["example"] = [example_note_response]
