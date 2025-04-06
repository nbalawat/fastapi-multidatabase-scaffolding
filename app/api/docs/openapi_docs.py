"""Enhanced OpenAPI documentation for the FastAPI application."""
from typing import Dict, Any, List, Type, Optional, Set
import inspect
import importlib
import pkgutil
import sys
from pathlib import Path

from fastapi import FastAPI, APIRouter
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

from app.models.notes.model import NoteVisibility
from app.models.users.model import Role
from app.core.permissions import get_permission_registry


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
    # Get current permissions and roles from the registry
    permission_registry = get_permission_registry()
    permissions = permission_registry.get_permissions()
    roles = permission_registry.get_roles()
    
    # Format permissions by category
    permission_categories = {}
    for perm_id, desc in permissions.items():
        category = perm_id.split(':')[0] if ':' in perm_id else 'other'
        if category not in permission_categories:
            permission_categories[category] = []
        permission_categories[category].append(f"{perm_id}: {desc}")
    
    # Format roles with their permissions
    roles_formatted = []
    for role_id, role_data in roles.items():
        role_perms = ', '.join([f"`{p}`" for p in role_data['permissions'][:3]])
        if len(role_data['permissions']) > 3:
            role_perms += f" and {len(role_data['permissions']) - 3} more"
        roles_formatted.append(f"- **{role_id}**: {role_data['description']} ({role_perms})")
    
    # Add database information
    schema["info"]["description"] = (
        "# FastAPI Multiple Databases\n\n"
        "This API supports multiple database backends including PostgreSQL, SQL Server, and MongoDB.\n\n"
        "## Database Types\n\n"
        "- **PostgreSQL**: Traditional relational database\n"
        "- **SQL Server**: Microsoft's enterprise relational database\n"
        "- **MongoDB**: NoSQL document database\n\n"
        "## Multi-Database Configuration\n\n"
        "The application can connect to multiple databases simultaneously. Each database is configured using environment variables:\n\n"
        "```\n"
        "# Primary database\n"
        "DB_TYPE=postgresql\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_USER=postgres\n"
        "DB_PASSWORD=password\n"
        "DB_NAME=fastapi\n\n"
        "# Additional databases\n"
        "DATABASES__users_db__DB_TYPE=mongodb\n"
        "DATABASES__users_db__DB_HOST=localhost\n"
        "DATABASES__products_db__DB_TYPE=sqlserver\n"
        "DATABASES__products_db__DB_HOST=localhost\n"
        "```\n\n"
        "## Authentication\n\n"
        "This API uses JWT tokens for authentication. To authenticate, use the `/api/v1/token` endpoint.\n\n"
        "## Role-Based Access Control\n\n"
        "The API implements a comprehensive role-based access control system with the following features:\n\n"
        "### Available Roles\n\n"
        f"{chr(10).join(roles_formatted)}\n\n"
        "### Permission System\n\n"
        "The system uses granular permissions for fine-grained access control. View all available permissions using the `/api/v1/roles-permissions` endpoint.\n\n"
        "#### Permission Categories:\n\n"
    )
    
    # Add permission categories to documentation
    permission_docs = ""
    for category, perms in permission_categories.items():
        permission_docs += f"**{category.capitalize()}**:\n"
        for perm in perms:
            permission_docs += f"- {perm}\n"
        permission_docs += "\n"
    
    schema["info"]["description"] += permission_docs
    schema["info"]["description"] += (
        "### Permission-Based Access\n\n"
        "API endpoints are protected based on specific permissions rather than just roles, allowing for more flexible access control.\n\n"
        "### Viewing Roles and Permissions\n\n"
        "Use the `/api/v1/roles-permissions` endpoint to view all available roles and permissions in the system.\n\n"
    )
    
    # Add model information to documentation
    models_by_module = discover_models()
    model_docs = "\n## Available Models\n\n"
    
    for module_name, models in sorted(models_by_module.items()):
        model_docs += f"### {module_name.capitalize()}\n\n"
        for model in sorted(models, key=lambda m: m.__name__):
            model_docs += f"- **{model.__name__}**: {model.__doc__ or 'No description available'}\n"
        model_docs += "\n"
    
    schema["info"]["description"] += model_docs
    
    # Add examples for all model endpoints
    add_model_examples(schema)
    
    # Add specific examples for notes endpoints
    add_notes_examples(schema)


def discover_models() -> Dict[str, List[Type[BaseModel]]]:
    """Discover all Pydantic models in the app.
    
    Returns:
        A dictionary mapping module names to lists of model classes
    """
    models_by_module: Dict[str, List[Type[BaseModel]]] = {}
    models_path = Path(__file__).parent.parent.parent / "models"
    
    # Walk through all modules in the models directory
    for module_info in pkgutil.iter_modules([str(models_path)]):
        if module_info.ispkg:  # Only process packages (e.g., notes, users)
            module_name = f"app.models.{module_info.name}"
            model_module_name = f"{module_name}.model"
            
            try:
                # Import the model module
                model_module = importlib.import_module(model_module_name)
                
                # Find all Pydantic models in the module
                models = []
                for name, obj in inspect.getmembers(model_module):
                    if (inspect.isclass(obj) and issubclass(obj, BaseModel) 
                            and obj.__module__ == model_module_name):
                        models.append(obj)
                
                if models:
                    models_by_module[module_info.name] = models
            except ImportError:
                # Skip if the model module doesn't exist
                pass
    
    return models_by_module


def discover_routers() -> List[APIRouter]:
    """Discover all API routers in the app.
    
    Returns:
        A list of router instances
    """
    routers = []
    models_path = Path(__file__).parent.parent.parent / "models"
    
    # Walk through all modules in the models directory
    for module_info in pkgutil.iter_modules([str(models_path)]):
        if module_info.ispkg:  # Only process packages
            module_name = f"app.models.{module_info.name}"
            router_module_name = f"{module_name}.router"
            
            try:
                # Import the router module
                router_module = importlib.import_module(router_module_name)
                
                # Find the router instance
                for name, obj in inspect.getmembers(router_module):
                    if isinstance(obj, APIRouter):
                        routers.append(obj)
                        break
            except ImportError:
                # Skip if the router module doesn't exist
                pass
    
    return routers


def add_model_examples(schema: Dict[str, Any]) -> None:
    """Add examples for all model endpoints to the OpenAPI schema.
    
    Args:
        schema: The OpenAPI schema
    """
    # Discover all models
    models_by_module = discover_models()
    paths = schema.get("paths", {})
    
    # Add examples for each model
    for module_name, models in models_by_module.items():
        # Find create and response models
        create_model = None
        response_model = None
        update_model = None
        
        for model in models:
            if model.__name__.endswith('Create'):
                create_model = model
            elif not model.__name__.endswith(('Create', 'Update')):
                response_model = model
            elif model.__name__.endswith('Update'):
                update_model = model
        
        if not (create_model and response_model):
            continue
            
        # Generate example instances
        try:
            # Create example data based on model fields
            example_data = {}
            for field_name, field in create_model.__fields__.items():
                # Get the field type in a safer way
                field_type = getattr(field, 'type_', None) or getattr(field, 'outer_type_', None)
                
                # Handle different field types
                if field_type == str or (hasattr(field_type, '__origin__') and field_type.__origin__ is str):
                    example_data[field_name] = f"Example {field_name}"
                elif field_type == int or (hasattr(field_type, '__origin__') and field_type.__origin__ is int):
                    example_data[field_name] = 42
                elif field_type == bool or (hasattr(field_type, '__origin__') and field_type.__origin__ is bool):
                    example_data[field_name] = True
                elif field_type == list or (hasattr(field_type, '__origin__') and field_type.__origin__ is list):
                    example_data[field_name] = ["example"]
                elif field_type == dict or (hasattr(field_type, '__origin__') and field_type.__origin__ is dict):
                    example_data[field_name] = {"key": "value"}
                else:
                    # Default to string for unknown types
                    example_data[field_name] = f"Example {field_name}"
            
            # Example response with ID and timestamps
            example_response = {
                **example_data,
                "id": "60d5ec9af682dbd12a0a9fb9",
                "created_at": "2023-04-04T12:00:00",
                "updated_at": None
            }
            
            # Example update data
            example_update = {}
            if update_model:
                for field_name, field in update_model.__fields__.items():
                    if field_name in example_data:
                        # Get the field type in a safer way
                        field_type = getattr(field, 'type_', None) or getattr(field, 'outer_type_', None)
                        
                        if field_type == str or (hasattr(field_type, '__origin__') and field_type.__origin__ is str):
                            example_update[field_name] = f"Updated {field_name}"
                        else:
                            example_update[field_name] = example_data[field_name]
            
            # Add examples to paths
            base_path = f"/api/v1/{module_name}"
            
            # POST /{module_name}
            if base_path in paths and "post" in paths[base_path]:
                if "requestBody" in paths[base_path]["post"] and "content" in paths[base_path]["post"]["requestBody"]:
                    paths[base_path]["post"]["requestBody"]["content"]["application/json"]["example"] = example_data
                
                for status_code in ["200", "201"]:
                    if status_code in paths[base_path]["post"]["responses"] and "content" in paths[base_path]["post"]["responses"][status_code]:
                        paths[base_path]["post"]["responses"][status_code]["content"]["application/json"]["example"] = example_response
            
            # GET /{module_name}/{id}
            item_path = f"{base_path}/{{item_id}}"
            if item_path in paths and "get" in paths[item_path]:
                if "200" in paths[item_path]["get"]["responses"] and "content" in paths[item_path]["get"]["responses"]["200"]:
                    paths[item_path]["get"]["responses"]["200"]["content"]["application/json"]["example"] = example_response
            
            # PUT /{module_name}/{id}
            if item_path in paths and "put" in paths[item_path]:
                if "requestBody" in paths[item_path]["put"] and "content" in paths[item_path]["put"]["requestBody"]:
                    paths[item_path]["put"]["requestBody"]["content"]["application/json"]["example"] = example_update
                
                if "200" in paths[item_path]["put"]["responses"] and "content" in paths[item_path]["put"]["responses"]["200"]:
                    updated_response = {**example_response, **example_update, "updated_at": "2023-04-04T12:30:00"}
                    paths[item_path]["put"]["responses"]["200"]["content"]["application/json"]["example"] = updated_response
            
            # GET /{module_name}
            if base_path in paths and "get" in paths[base_path]:
                if "200" in paths[base_path]["get"]["responses"] and "content" in paths[base_path]["get"]["responses"]["200"]:
                    paths[base_path]["get"]["responses"]["200"]["content"]["application/json"]["example"] = [example_response]
                    
        except Exception as e:
            # Skip if we can't generate examples
            print(f"Error generating examples for {module_name}: {e}")
            continue


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
