"""
Base service and permission decorators
"""

from functools import wraps
from typing import Any, Callable, TypeVar

from django.core.exceptions import PermissionDenied

T = TypeVar("T")


def requires_permission(permission_type: str, obj_param: str = "instance"):
    """
    Permission decorator for service methods.

    Args:
        permission_type: Type of permission to check (view/edit/delete)
        obj_param: Name of the parameter that contains the object to check permissions against
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(service: Any, user: Any, *args, **kwargs) -> Any:
            # Get the object to check permissions against
            obj = kwargs.get(obj_param) or (args[0] if args else None)
            if not obj:
                raise ValueError(f"Could not find object parameter: {obj_param}")

            # Get the permission check method
            check_method = getattr(service, f"can_{permission_type}")
            if not check_method:
                raise ValueError(f"Service does not implement: can_{permission_type}")

            # Check permission
            if not check_method(user, obj):
                raise PermissionDenied(
                    f"User does not have {permission_type} permission for {obj}"
                )

            return func(service, user, *args, **kwargs)

        return wrapper

    return decorator


class BasePermissionService:
    """Base service class with permission checks"""

    def can_view(self, user: Any, instance: Any) -> bool:
        raise NotImplementedError

    def can_edit(self, user: Any, instance: Any) -> bool:
        raise NotImplementedError

    def can_delete(self, user: Any, instance: Any) -> bool:
        raise NotImplementedError

    def can_create(self, user: Any) -> bool:
        raise NotImplementedError
