from typing import Type, Callable, TypeVar, Dict, Any, List, Optional, Generic
from fastapi import APIRouter, Depends, HTTPException, Query
import logging
from pydantic import BaseModel

from app.utils.generic.base_controller import BaseController
from app.core.security import RBACMiddleware
from app.core.permissions import get_permission_registry

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)
U = TypeVar('U', bound=BaseModel)
V = TypeVar('V', bound=BaseModel)

def create_standard_routes(
    router: APIRouter,
    controller_class: Type[BaseController],
    create_model: Type[T],
    update_model: Type[U],
    response_model: Type[V],
    get_db_adapter: Callable,
    permissions: Dict[str, List[str]] = None,
    enable_rbac: bool = False
):
    """Create standard CRUD routes for a model.
    
    Args:
        router: The FastAPI router to add routes to
        controller_class: The controller class to use
        create_model: The model class for create operations
        update_model: The model class for update operations
        response_model: The model class for responses
        get_db_adapter: Function to get the database adapter
        permissions: Dictionary mapping endpoint names to required permissions
        enable_rbac: Whether to enable RBAC for these routes
    """
    model_name = response_model.__name__.lower()
    
    # Default permissions if not specified
    if permissions is None:
        permissions = {}
        
    default_permissions = {
        "create": [f"{model_name}:create"],
        "read": [f"{model_name}:read"],
        "update": [f"{model_name}:update"],
        "delete": [f"{model_name}:delete"],
        "list": [f"{model_name}:read"]
    }
    
    # Register any new permissions with the registry
    permission_registry = get_permission_registry()
    for operation, perms in default_permissions.items():
        for perm in perms:
            if not permission_registry.validate_permission(perm):
                permission_registry.register_permission(
                    permission_id=perm,
                    description=f"{operation.capitalize()} {model_name}"
                )
    
    # Merge default permissions with provided permissions
    for key, value in default_permissions.items():
        if key not in permissions:
            permissions[key] = value
    
    # Create route with or without RBAC
    if enable_rbac:
        @router.post("/", response_model=response_model)
        async def create_item(
            item: create_model, 
            db_adapter=Depends(get_db_adapter),
            user=Depends(RBACMiddleware.has_permission(permissions["create"]))
        ):
            """Create a new item."""
            controller = controller_class(db_adapter)
            result = await controller.create(item)
            return result
    else:
        @router.post("/", response_model=response_model)
        async def create_item(item: create_model, db_adapter=Depends(get_db_adapter)):
            """Create a new item."""
            controller = controller_class(db_adapter)
            result = await controller.create(item)
            return result

    # Read route with or without RBAC
    if enable_rbac:
        @router.get("/{item_id}", response_model=response_model)
        async def read_item(
            item_id: str, 
            db_adapter=Depends(get_db_adapter),
            user=Depends(RBACMiddleware.has_permission(permissions["read"]))
        ):
            """Get an item by ID."""
            controller = controller_class(db_adapter)
            result = await controller.read(item_id)
            
            if not result:
                raise HTTPException(status_code=404, detail=f"{model_name} with ID {item_id} not found")
                
            return result
    else:
        @router.get("/{item_id}", response_model=response_model)
        async def read_item(item_id: str, db_adapter=Depends(get_db_adapter)):
            """Get an item by ID."""
            controller = controller_class(db_adapter)
            result = await controller.read(item_id)
            
            if not result:
                raise HTTPException(status_code=404, detail=f"{model_name} with ID {item_id} not found")
                
            return result

    # Update route with or without RBAC
    if enable_rbac:
        @router.put("/{item_id}", response_model=response_model)
        async def update_item(
            item_id: str, 
            item: update_model, 
            db_adapter=Depends(get_db_adapter),
            user=Depends(RBACMiddleware.has_permission(permissions["update"]))
        ):
            """Update an item by ID."""
            controller = controller_class(db_adapter)
            result = await controller.update(item_id, item)
            
            if not result:
                raise HTTPException(status_code=404, detail=f"{model_name} with ID {item_id} not found")
                
            return result
    else:
        @router.put("/{item_id}", response_model=response_model)
        async def update_item(item_id: str, item: update_model, db_adapter=Depends(get_db_adapter)):
            """Update an item by ID."""
            controller = controller_class(db_adapter)
            result = await controller.update(item_id, item)
            
            if not result:
                raise HTTPException(status_code=404, detail=f"{model_name} with ID {item_id} not found")
                
            return result

    # Delete route with or without RBAC
    if enable_rbac:
        @router.delete("/{item_id}", response_model=bool)
        async def delete_item(
            item_id: str, 
            db_adapter=Depends(get_db_adapter),
            user=Depends(RBACMiddleware.has_permission(permissions["delete"]))
        ):
            """Delete an item by ID."""
            controller = controller_class(db_adapter)
            result = await controller.delete(item_id)
            
            if not result:
                raise HTTPException(status_code=404, detail=f"{model_name} with ID {item_id} not found")
                
            return result
    else:
        @router.delete("/{item_id}", response_model=bool)
        async def delete_item(item_id: str, db_adapter=Depends(get_db_adapter)):
            """Delete an item by ID."""
            controller = controller_class(db_adapter)
            result = await controller.delete(item_id)
            
            if not result:
                raise HTTPException(status_code=404, detail=f"{model_name} with ID {item_id} not found")
                
            return result

    # List route with or without RBAC
    if enable_rbac:
        @router.get("/", response_model=List[response_model])
        async def list_items(
            skip: int = 0, 
            limit: int = 100, 
            db_adapter=Depends(get_db_adapter),
            user=Depends(RBACMiddleware.has_permission(permissions["list"]))
        ):
            """List items with optional filtering."""
            controller = controller_class(db_adapter)
            result = await controller.list(skip, limit)
            return result
    else:
        @router.get("/", response_model=List[response_model])
        async def list_items(
            skip: int = 0, 
            limit: int = 100, 
            db_adapter=Depends(get_db_adapter)
        ):
            """List items with optional filtering."""
            controller = controller_class(db_adapter)
            result = await controller.list(skip, limit)
            return result
