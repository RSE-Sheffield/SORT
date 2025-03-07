"""
Project service with integrated permissions
"""

from typing import Optional, Dict
from django.db.models.query import QuerySet
from django.core.exceptions import PermissionDenied

from ..constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from ..models import (
    Organisation,
    Project,
    User,
)
from .base import BasePermissionService, requires_permission


class ProjectService(BasePermissionService):
    """Service for managing projects with integrated permissions"""

    def get_user_role(self, user: User, project: Project) -> Optional[str]:
        """Get user's role in the project's organisation"""
        try:
            return project.organisation.get_user_role(user)
        except (
            AttributeError
        ):  # In case user is AnonymousUser or organisation method fails
            return None

    def can_view(self, user: User, project: Project) -> bool:
        """All organization members can view projects"""
        role = self.get_user_role(user, project)
        return role in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]

    def can_edit(self, user: User, project: Project) -> bool:
        role = self.get_user_role(user, project)
        return role in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]

    def can_create(self, user: User) -> bool:
        org = user.organisation_set.first()
        role = org.get_user_role(user)
        return role in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]

    def can_delete(self, user: User, project: Project) -> bool:
        """Only admins can delete projects"""
        role = self.get_user_role(user, project)
        return role == ROLE_ADMIN

    @requires_permission("edit", obj_param="project")
    def update_project(self, user: User, project: Project, data: Dict) -> Project:
        """Update project with provided data"""
        for key, value in data.items():
            setattr(project, key, value)
        project.save()
        return project

    @requires_permission("view", obj_param="project")
    def get_project(self, user: User, project: Project) -> Project:
        """Get project if user has permission"""
        return project

    def create_project(
        self, user: User, name: str, organisation: Organisation, description: str = ""
    ) -> Project:
        """Create a new project"""
        if not self.can_create(user):
            raise PermissionDenied("User cannot create projects")

        project = Project.objects.create(
            name=name,
            description=description,
            created_by=user,
            organisation=organisation,
        )
        return project

    def delete_project(self, user: User, project: Project):
        """Delete a project"""
        if not self.can_delete(user, project):
            raise PermissionDenied("User cannot delete projects")

        organisation = project.organisation
        project.delete()
        return organisation

    def get_user_projects(self, user: User) -> QuerySet[Project]:
        """Get all projects a user has access to"""
        # Get all organisations the user is a member of
        user_orgs = user.organisation_set.all()
        return Project.objects.filter(organisation__in=user_orgs)
