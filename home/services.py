"""
This module contains the business logic and data operations.

Services files are responsible for:
- Implementing business logic
- Handling data operations
- Coordinating between different parts of the system
- Providing an interface for views to access functionality

Services should:
- Be organised by domain/model
- Handle complex operations
- Not contain permission checks (use permissions.py)
- Not contain presentation logic (use views)

Example usage:
    org_service = OrganisationService()
    user_org = org_service.get_user_organisation(user)
    projects = org_service.get_organisation_projects(user_org)
"""

from .models import (
    ProjectManagerPermission,
    Organisation,
    OrganisationMembership,
    Project,
    ProjectOrganisation,
    User,
)
from typing import Dict, List, Literal, Set, Optional, Union
from django.db.models.query import QuerySet
from django.db.models import Count
from .constants import ROLE_PROJECT_MANAGER, ROLE_ADMIN


class ProjectService:
    """
    Service class for managing project operations and permissions
    """

    @staticmethod
    def get_user_permission(
        project: Project, user: User
    ) -> Optional[ProjectManagerPermission]:
        """Get user's permission level for a specific project"""
        
        return ProjectManagerPermission.objects.filter(
            user=user, project=project
        ).first()

    @staticmethod
    def grant_permission(
        project: Project,
        project_manager: User,
        granted_by: User,
        permission: Literal["VIEW", "EDIT"] = "VIEW",
    ) -> tuple[ProjectManagerPermission, bool]:
        """
        Grant project permission to a project manager
        Returns tuple of (permission_object, created)
        """
        if permission not in ["VIEW", "EDIT"]:
            raise ValueError("Permission must be either VIEW or EDIT")

        # Verify user is a project manager in one of the project's organisations
        if not project_manager.organisationmembership_set.filter(
            organisation__projectorganisation__project=project,
            role=ROLE_PROJECT_MANAGER,
        ).exists():
            raise ValueError(
                "User must be a project manager in one of the project's organisations"
            )

        return ProjectManagerPermission.objects.update_or_create(
            user=project_manager,
            project=project,
            defaults={"granted_by": granted_by, "permission": permission},
        )

    @staticmethod
    def revoke_permission(project: Project, project_manager: User) -> tuple[int, dict]:
        """
        Revoke all permissions for a project manager on a project
        Returns tuple of (deleted_count, deleted_objects_by_type)
        """
        return ProjectManagerPermission.objects.filter(
            user=project_manager, project=project
        ).delete()

    @staticmethod
    def link_project_to_organisation(
        project: Project,
        organisation: Organisation,
        user: User,
        permission: Literal["VIEW", "EDIT"] = "EDIT",
    ) -> ProjectOrganisation:
        """
        Links a project to an organisation and handles project manager permissions
        Also grants appropriate permissions if user is a project manager
        """
        project_org = ProjectOrganisation.objects.create(
            project=project, organisation=organisation, added_by=user
        )

        # Handle project manager permissions if applicable
        user_role = organisation.get_user_role(user)
        if user_role == ROLE_PROJECT_MANAGER:
            ProjectService.grant_permission(
                project=project,
                project_manager=user,
                granted_by=user,
                permission=permission,
            )

        return project_org

    @staticmethod
    def get_user_projects(user: User) -> QuerySet[Project]:
        """Get all projects a user has access to"""
        return Project.objects.filter(projectmanagerpermission__user=user).distinct()


class OrganisationService:
    """
    Service class for managing organisation operations and access
    """

    @staticmethod
    def get_user_organisation(user: User) -> Optional[Organisation]:
        """Get user's primary organisation"""
        return user.organisation_set.first()

    @staticmethod
    def get_user_organisation_ids(user: User) -> Set[int]:
        """Get IDs of organisations user belongs to"""
        return set(
            OrganisationMembership.objects.filter(user=user).values_list(
                "organisation_id", flat=True
            )
        )

    @staticmethod
    def get_user_accessible_organisations(
        projects: QuerySet[Project], user: User
    ) -> Dict[int, List[Organisation]]:
        """Get organisations for each project that user is member of"""
        user_org_ids = OrganisationService.get_user_organisation_ids(user)
        return {
            project.id: [
                org for org in project.organisations.all() if org.id in user_org_ids
            ]
            for project in projects
        }

    @staticmethod
    def get_organisation_projects(
        organisation: Organisation, with_metrics: bool = True
    ) -> QuerySet[Project]:
        """
        Get projects for an organisation, optionally with metrics
        Metrics include: survey count, manager count
        """
        projects = Project.objects.filter(
            projectorganisation__organisation=organisation
        )

        if with_metrics:
            projects = projects.annotate(
                survey_count=Count("survey"),
                manager_count=Count("projectmanagerpermission", distinct=True),
            )

        return projects

    @staticmethod
    def add_user_to_organisation(
        user: User,
        organisation: Organisation,
        role: Literal["ADMIN", "PROJECT_MANAGER"],
        added_by: User,
    ) -> OrganisationMembership:
        """Add a user to an organisation with specified role"""
        if role not in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]:
            raise ValueError(
                f"Role must be either {ROLE_ADMIN} or {ROLE_PROJECT_MANAGER}"
            )

        return OrganisationMembership.objects.create(
            user=user, organisation=organisation, role=role
        )

    @staticmethod
    def remove_user_from_organisation(
        user: User, organisation: Organisation
    ) -> tuple[int, dict]:
        """
        Remove user from organisation and cleanup related permissions
        Returns tuple of (deleted_count, deleted_objects_by_type)
        """
        # First revoke all project permissions in this org
        ProjectManagerPermission.objects.filter(
            user=user, project__organisations=organisation
        ).delete()

        # Then remove org membership
        return OrganisationMembership.objects.filter(
            user=user, organisation=organisation
        ).delete()

    @staticmethod
    def get_organisation_members(
        organisation: Organisation,
    ) -> QuerySet[OrganisationMembership]:
        """Get all members of an organisation with their roles"""
        return OrganisationMembership.objects.filter(
            organisation=organisation
        ).select_related("user")
