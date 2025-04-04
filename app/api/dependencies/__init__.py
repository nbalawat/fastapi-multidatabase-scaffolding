"""Dependencies for the API."""
from app.api.dependencies.auth import (
    get_db_adapter,
    get_user,
    authenticate_user,
    get_current_user,
    get_current_active_user
)
from app.api.dependencies.permissions import (
    has_permission,
    has_any_permission,
    has_all_permissions,
    get_user_permissions
)

__all__ = [
    "get_db_adapter",
    "get_user",
    "authenticate_user",
    "get_current_user",
    "get_current_active_user",
    "has_permission",
    "has_any_permission",
    "has_all_permissions",
    "get_user_permissions"
]
