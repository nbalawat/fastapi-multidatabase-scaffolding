# RBAC Configuration Guide

This document explains how to configure Role-Based Access Control (RBAC) in the application.

## Permission Registry

The application uses a centralized permission registry to manage and validate permissions and roles. This ensures that:

1. All permissions are well-defined and documented
2. Roles contain only valid permissions
3. Permission checks are consistent across the application

## Static Configuration vs. Database Storage

The application supports two approaches for permission and role management:

### 1. Static Configuration (Default)

By default, permissions and roles are defined in `app/core/permissions.py`. This approach:

- Provides a single source of truth for all permissions and roles
- Makes permission changes part of the codebase (version controlled)
- Simplifies deployment (no database migration needed for permission changes)
- Works well for applications with a fixed set of permissions

```python
# Example of static permission configuration
PERMISSIONS = {
    "notes:create": "Create new notes",
    "notes:read": "Read notes",
    "notes:update": "Update existing notes",
    "notes:delete": "Delete notes",
    # ...
}

ROLES = {
    "admin": {
        "description": "Administrator with full access",
        "permissions": [
            "notes:create", "notes:read", "notes:update", "notes:delete",
            # ...
        ]
    },
    # ...
}
```

### 2. Database Storage (Optional)

For applications that need dynamic permission management, you can store permissions and roles in the database:

1. Create database tables for permissions and roles
2. Implement a service to manage permissions and roles
3. Update the permission registry to load from the database

This approach is useful when:
- Permissions need to be managed by administrators at runtime
- You need to create custom roles for specific users
- Permission requirements change frequently

## Auto-Registration of Permissions

The application automatically registers permissions used in route definitions:

```python
# When creating standard routes
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
        "update": ["notes:update"],
        "delete": ["notes:delete"],
        "list": ["notes:read"]
    },
    enable_rbac=True
)
```

When this code runs, the permission registry will:
1. Check if each permission exists
2. Register any new permissions with a default description
3. Log warnings for any invalid permissions

## Permission Naming Convention

Permissions follow a `resource:action` naming convention:

- `notes:create` - Create notes
- `users:read` - Read user information
- `roles:assign` - Assign roles to users

This convention makes permissions intuitive and easy to understand.

## Validation and Error Handling

The RBAC system validates permissions and roles at multiple levels:

1. **Static Validation**: When the application starts, it validates that all roles reference valid permissions
2. **Route Definition Validation**: When routes are defined, it validates that all required permissions exist
3. **Runtime Validation**: When a request is made, it validates that the user has the required permissions

Invalid permissions or roles are logged as warnings but don't break the application. This ensures that:

1. Developers are alerted to permission configuration issues
2. The application remains stable even with misconfigured permissions
3. Security is maintained (invalid permissions don't grant access)

## Implementing Database-Backed Permissions

To implement database-backed permissions:

1. Create database models for permissions and roles
2. Implement a service to manage permissions and roles
3. Update the permission registry to load from the database
4. Add endpoints for permission and role management

See the example implementation in the `examples/database_permissions` directory.
