# Router Utilities

## Overview

The Router Utilities module provides a powerful abstraction for creating standardized API endpoints in the FastAPI application. This module follows the DRY (Don't Repeat Yourself) principle by centralizing route creation logic, making it easier to maintain consistent API patterns across the application.

## Key Features

- **Automatic Route Generation**: Create all standard CRUD routes with a single function call
- **Role-Based Access Control (RBAC)**: Optional integration with the application's permission system
- **Type Safety**: Uses generics to ensure type safety across models
- **Consistent Error Handling**: Standardized 404 responses when items aren't found
- **Permission Management**: Automatic registration of permissions for each operation

## Using `create_standard_routes()`

The main function provided by this module is `create_standard_routes()`, which automatically generates five standard endpoints for a model:

- **POST** `/`: Create a new item
- **GET** `/{item_id}`: Get an item by ID
- **PUT** `/{item_id}`: Update an item
- **DELETE** `/{item_id}`: Delete an item
- **GET** `/`: List all items

### Basic Usage

```python
from app.utils.generic.router_utils import create_standard_routes

# Create a router
router = APIRouter(prefix="/users", tags=["users"])

# Generate standard CRUD routes
create_standard_routes(
    router=router,
    controller_class=UsersController,
    create_model=UserCreate,
    update_model=UserUpdate,
    response_model=User,
    get_db_adapter=get_db_adapter
)
```

### With Role-Based Access Control

```python
# Define custom permissions
permissions = {
    "create": ["admin:create_user"],
    "read": ["user:read"],
    "update": ["admin:update_user"],
    "delete": ["admin:delete_user"],
    "list": ["user:list"]
}

# Generate routes with RBAC
create_standard_routes(
    router=router,
    controller_class=UsersController,
    create_model=UserCreate,
    update_model=UserUpdate,
    response_model=User,
    get_db_adapter=get_db_adapter,
    permissions=permissions,
    enable_rbac=True
)
```

## When to Use Router Utilities vs. Custom Routes

### Use Router Utilities When:

- You need standard CRUD operations without customization
- You want consistent API patterns across your application
- You're implementing a new resource that follows standard patterns

### Create Custom Routes When:

- You need custom behavior, like setting the user_id from authentication
- You have specialized validation or processing logic
- You need to implement non-standard endpoints

## Example: Custom Routes for Authentication-Dependent Operations

In some cases, you may need to customize route behavior beyond what the utilities provide. For example, when creating notes that should be associated with the authenticated user:

```python
@router.post("/", response_model=Note)
async def create_note(
    note: NoteCreate,
    db_adapter=Depends(get_db_adapter),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new note with the current user's ID."""
    controller = NotesController(db_adapter)
    # Pass the current user to the controller
    result = await controller.create_with_user(note, current_user)
    return result
```

## UUID Handling in Responses

The application includes automatic UUID conversion in the BaseController, which ensures that any UUID objects in responses are properly converted to strings. This is particularly important when working with user IDs and other UUID fields.

## Best Practices

1. **Consistent Naming**: Use consistent naming for your models (e.g., `NoteCreate`, `NoteUpdate`, `Note`)
2. **Controller Design**: Implement model-specific logic in the controller, not in the routes
3. **Permission Granularity**: Define permissions at an appropriate level of granularity
4. **Documentation**: Always include docstrings for your routes, even when generated automatically

## API Reference

### `create_standard_routes()`

```python
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
    """Create standard CRUD routes for a model."""
```

#### Parameters:

- **router**: The FastAPI router to add routes to
- **controller_class**: The controller class to use
- **create_model**: The model class for create operations
- **update_model**: The model class for update operations
- **response_model**: The model class for responses
- **get_db_adapter**: Function to get the database adapter
- **permissions**: Dictionary mapping endpoint names to required permissions
- **enable_rbac**: Whether to enable RBAC for these routes
