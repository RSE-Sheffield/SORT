from typing import Literal

ROLE_ADMIN = "ADMIN"
ROLE_PROJECT_MANAGER = "PROJECT_MANAGER"

ROLES = [
    (ROLE_ADMIN, "Admin"),
    (ROLE_PROJECT_MANAGER, "Project Manager"),
]
"""
ADMIN: Full control over organisation and all projects
PROJECT_MANAGER: Can manage specific projects with view or edit permissions
"""

RoleType = Literal["ADMIN", "PROJECT_MANAGER"]

PERMISSION_VIEW = "VIEW"
PERMISSION_EDIT = "EDIT"

PERMISSION_CHOICES = [
    (PERMISSION_VIEW, "View Only"),
    (PERMISSION_EDIT, "View and Edit"),
]