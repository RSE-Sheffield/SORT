"""
This module handles permission checking logic.

Permissions files define who can do what in the system. They contain functions that:
- Check if users have specific permissions
- Validate access rights
- Determine role-based capabilities
- Handle authorization logic

These functions should:
- Take a user and the object to check permissions against
- Return boolean or permission mapping results
- Be pure functions when possible (same input always gives same output)
- Not contain business logic (that belongs in services)
"""

from typing import Optional, Dict
from django.db.models.query import QuerySet
from .models import Project, User
from .constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from .services import ProjectService, OrganisationService


def get_user_role_in_project(user: User, project: Project) -> Optional[str]:
    """Get user's highest role across project's organisations"""
    project_orgs = project.organisations.all()
    for org in project_orgs:
        role = org.get_user_role(user)
        if role == ROLE_ADMIN:
            return ROLE_ADMIN
    # Return PROJECT_MANAGER if found in any org, otherwise None
    return next(
        (
            org.get_user_role(user)
            for org in project_orgs
            if org.get_user_role(user) == ROLE_PROJECT_MANAGER
        ),
        None,
    )


def can_view_project(user: User, project: Project) -> bool:
    """
    Check if user can view the project:
        - ADMIN: Can always view if they're in the project's organisations
        - PROJECT_MANAGER: Can view if they have explicit permission
    """
    role = get_user_role_in_project(user, project)

    if role == ROLE_ADMIN:
        return True
    elif role == ROLE_PROJECT_MANAGER:
        return ProjectService.get_user_permission(project, user) is not None

    return False


def can_edit_project(user: User, project: Project) -> bool:
    """
    Check if user can edit the project:
        - ADMIN: Can always edit if they're in the project's organisations
        - PROJECT_MANAGER: Can only edit if they have explicit EDIT permission
    """
    role = get_user_role_in_project(user, project)

    if role == ROLE_ADMIN:
        return True
    elif role == ROLE_PROJECT_MANAGER:
        permission = ProjectService.get_user_permission(project, user)
        return permission and permission.permission == "EDIT"

    return False


def can_create_projects(user: User) -> bool:
    """Check if user can create projects based on admin role"""
    org = OrganisationService.get_user_organisation(user)
    return org and org.get_user_role(user) == ROLE_ADMIN


def get_project_permissions(user: User, projects: QuerySet[Project]) -> Dict[int, bool]:
    """Get edit permissions for multiple projects"""
    return {project.id: can_edit_project(user, project) for project in projects}
