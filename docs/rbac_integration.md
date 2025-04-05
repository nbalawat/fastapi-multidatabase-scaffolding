# RBAC Integration with Model-Centric Architecture

This document explains how Role-Based Access Control (RBAC) is integrated with the model-centric architecture.

## Overview

The RBAC system is designed to work seamlessly with our model-centric architecture, allowing for:

1. **Permission-Based Access Control**: Control access to resources based on permissions
2. **Role-Based Access Control**: Group permissions into roles for easier management
3. **Flexible Configuration**: Enable or disable RBAC for specific routes or models
4. **Consistent Interface**: Use the same patterns across all models

## Key Components

### 1. RBAC Middleware

The `RBACMiddleware` class in `app/utils/security/rbac.py` provides the core RBAC functionality:

- `has_permission`: Check if a user has specific permissions
- `has_role`: Check if a user has specific roles

```python
# Example of using the RBAC middleware directly
@router.get("/protected")
async def protected_route(user=Depends(RBACMiddleware.has_permission(["notes:read"]))):
    return {"message": "You have access to this route"}
```

### 2. Router Utilities with RBAC Support

The `create_standard_routes` function in `app/utils/generic/router_utils.py` has been updated to support RBAC:

```python
create_standard_routes(
    router=router,
    controller_class=NotesController,
    create_model=NoteCreate,
    update_model=NoteUpdate,
    response_model=Note,
    get_db_adapter=get_db_adapter,
    permissions={
        "create": ["notes:create"],
        "read": ["notes:read"],
        "update": ["notes:update", "notes:admin"],
        "delete": ["notes:delete", "notes:admin"],
        "list": ["notes:read"]
    },
    enable_rbac=True
)
```

### 3. Custom RBAC for Model-Specific Routes

For custom routes, you can use the RBAC middleware directly:

```python
@router.get("/by-tag/{tag}", response_model=List[Note])
async def get_notes_by_tag(
    tag: str,
    skip: int = 0,
    limit: int = 100,
    db_adapter=Depends(get_db_adapter),
    user=Depends(RBACMiddleware.has_permission(["notes:read"]))
):
    """Get notes by tag."""
    controller = NotesController(db_adapter)
    result = await controller.list(skip, limit, {"tag": tag})
    return result
```

## Default Permissions

The system automatically generates default permissions based on the model name:

- `{model_name}:create`: Permission to create new items
- `{model_name}:read`: Permission to read items
- `{model_name}:update`: Permission to update items
- `{model_name}:delete`: Permission to delete items

These default permissions can be overridden by providing a custom `permissions` dictionary.

## User Model Integration

The User model is responsible for storing user roles and permissions:

```python
class User(BaseModel):
    id: str
    username: str
    email: str
    hashed_password: str
    roles: List[str] = []
    permissions: List[str] = []
    is_active: bool = True
```

## Implementing RBAC in a New Model

To implement RBAC for a new model:

1. Create your model, controller, and router as usual
2. Enable RBAC in the `create_standard_routes` call:

```python
# app/models/comments/router.py
create_standard_routes(
    router=router,
    controller_class=CommentsController,
    create_model=CommentCreate,
    update_model=CommentUpdate,
    response_model=Comment,
    get_db_adapter=get_db_adapter,
    permissions={
        "create": ["comments:create"],
        "read": ["comments:read"],
        "update": ["comments:update"],
        "delete": ["comments:delete"],
        "list": ["comments:read"]
    },
    enable_rbac=True
)
```

3. For custom routes, use the RBAC middleware directly:

```python
@router.get("/by-note/{note_id}", response_model=List[Comment])
async def get_comments_by_note(
    note_id: str,
    db_adapter=Depends(get_db_adapter),
    user=Depends(RBACMiddleware.has_permission(["comments:read"]))
):
    """Get comments by note ID."""
    controller = CommentsController(db_adapter)
    result = await controller.list(0, 100, {"note_id": note_id})
    return result
```

## Best Practices

1. **Granular Permissions**: Define permissions at a granular level (e.g., `notes:create`, `notes:read`)
2. **Role-Based Design**: Group permissions into roles for easier management
3. **Consistent Naming**: Use consistent naming for permissions across models
4. **Documentation**: Document the permissions required for each endpoint
5. **Testing**: Test RBAC functionality thoroughly to ensure proper access control
