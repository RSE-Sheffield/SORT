"""
Project service with integrated permissions
"""

from typing import Optional, Dict, Tuple, Literal
from django.db.models.query import QuerySet
from .base import BasePermissionService, requires_permission
from ..models import (
    Project,
    User,
    Organisation,
    ProjectManagerPermission,
    ProjectOrganisation,
)
from ..constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from django.core.exceptions import PermissionDenied


class ProjectService(BasePermissionService):
    """Service for managing projects with integrated permissions"""

    def get_user_role(self, user: User, project: Project) -> Optional[str]:
        """Get user's highest role across project's organisations"""
        project_orgs = project.organisations.all()

        # Check for admin role first
        for org in project_orgs:
            role = org.get_user_role(user)
            if role == ROLE_ADMIN:
                return ROLE_ADMIN

        # Then check for project manager role
        return next(
            (
                org.get_user_role(user)
                for org in project_orgs
                if org.get_user_role(user) == ROLE_PROJECT_MANAGER
            ),
            None,
        )

    def get_user_permission(
        self, user: User, project: Project
    ) -> Optional[ProjectManagerPermission]:
        """Get user's permission level for a project"""
        return ProjectManagerPermission.objects.filter(
            user=user, project=project
        ).first()

    def can_view(self, user: User, project: Project) -> bool:
        role = self.get_user_role(user, project)

        if role == ROLE_ADMIN:
            return True
        elif role == ROLE_PROJECT_MANAGER:
            return self.get_user_permission(user, project) is not None

        return False

    def can_edit(self, user: User, project: Project) -> bool:
        role = self.get_user_role(user, project)

        if role == ROLE_ADMIN:
            return True
        elif role == ROLE_PROJECT_MANAGER:
            permission = self.get_user_permission(user, project)
            return permission and permission.permission == "EDIT"

        return False

    def can_create(self, user: User) -> bool:
        org = user.organisation_set.first()
        return org and org.get_user_role(user) == ROLE_ADMIN

    def can_delete(self, user: User, project: Project) -> bool:
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
            name=name, description=description, created_by=user
        )
        self.link_project_to_organisation(
            user=user, project=project, organisation=organisation, permission="EDIT"
        )
        return project

    def delete_project(self, user: User, project: Project):
        if not self.can_delete(user, project):
            raise PermissionDenied("User cannot delete projects")

        parent_org = project.organisations.first()
        project.delete()
        return parent_org

    @requires_permission("edit", obj_param="project")
    def grant_permission(
        self,
        user: User,
        project: Project,
        project_manager: User,
        permission: Literal["VIEW", "EDIT"] = "VIEW",
    ) -> Tuple[ProjectManagerPermission, bool]:
        """Grant project permission to a project manager"""

        if permission not in ["VIEW", "EDIT"]:
            raise ValueError("Permission must be either VIEW or EDIT")

        if not project_manager.organisationmembership_set.filter(
            organisation__projectorganisation__project=project,
            role=ROLE_PROJECT_MANAGER,
        ).exists():
            raise ValueError("User must be a project manager")

        return ProjectManagerPermission.objects.update_or_create(
            user=project_manager,
            project=project,
            defaults={"granted_by": user, "permission": permission},
        )

    @requires_permission("edit", obj_param="project")
    def revoke_permission(
        self, user: User, project: Project, project_manager: User
    ) -> None:
        """Revoke permissions for a project manager"""
        ProjectManagerPermission.objects.filter(
            user=project_manager, project=project
        ).delete()

    def link_project_to_organisation(
        self,
        user: User,
        project: Project,
        organisation: Organisation,
        permission: Literal["VIEW", "EDIT"] = "EDIT",
    ) -> ProjectOrganisation:
        """Link project to organisation and handle permissions"""
        project_org = ProjectOrganisation.objects.create(
            project=project, organisation=organisation, added_by=user
        )

        user_role = organisation.get_user_role(user)
        if user_role == ROLE_PROJECT_MANAGER:
            self.grant_permission(
                user=user, project=project, project_manager=user, permission=permission
            )

        return project_org

    def get_user_projects(self, user: User) -> QuerySet[Project]:
        """Get all projects a user has access to"""
        return Project.objects.filter(projectmanagerpermission__user=user).distinct()
