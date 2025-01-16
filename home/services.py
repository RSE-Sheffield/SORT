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
    GuestProjectAccess,
    Organisation,
    OrganisationMembership,
    Project,
    User,
)
from typing import Dict, List, Set
from django.db.models.query import QuerySet
from django.db.models import Count


class OrganisationService:
    @staticmethod
    def get_user_organisation(user: User) -> Organisation:
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
    def get_organisation_projects(organisation: Organisation) -> QuerySet[Project]:
        """Get projects for an organisation with survey count"""
        return Project.objects.filter(
            projectorganisation__organisation=organisation
        ).annotate(survey_count=Count("survey"))


class OrganisationAccessService:

    @staticmethod
    def get_user_accessible_organisations(
        projects: QuerySet[Project], user_org_ids: Set[int]
    ) -> Dict[int, List[Organisation]]:
        """Get organisations for each project that user is member of"""
        return {
            project.id: [
                org for org in project.organisations.all() if org.id in user_org_ids
            ]
            for project in projects
        }


class ProjectAccessService:
    """
    Service class for managing project access permissions for GUEST users
    """

    @staticmethod
    def grant_guest_access(
        project: Project, guest_user: User, granted_by: User, permission="VIEW"
    ):
        if permission not in ["VIEW", "EDIT"]:
            raise ValueError("Permission must be either VIEW or EDIT")

        if not guest_user.organisationmembership_set.filter(
            organisation__projectorganisation__project=project, role="GUEST"
        ).exists():
            raise ValueError(
                "User must be a guest in one of the project's organisations"
            )

        return GuestProjectAccess.objects.update_or_create(
            user=guest_user,
            project=project,
            defaults={"granted_by": granted_by, "permission": permission},
        )

    @staticmethod
    def revoke_guest_access(project, guest_user):
        return GuestProjectAccess.objects.filter(
            user=guest_user, project=project
        ).delete()
