"""
Organisation service with integrated permissions
"""

from typing import Optional, Dict, List, Set, Literal
from django.db import transaction
from django.db.models.query import QuerySet
from django.db.models import Count
from django.core.exceptions import PermissionDenied
from .base import BasePermissionService, requires_permission
from ..models import (
    Organisation,
    User,
    OrganisationMembership,
    Project,
    ProjectManagerPermission,
)
from ..constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER


class OrganisationService(BasePermissionService):
    """Service for managing organisations with integrated permissions"""

    def get_user_role(self, user: User, organisation: Organisation) -> Optional[str]:
        membership = organisation.organisationmembership_set.filter(user=user).first()
        return membership.role if membership else None

    def can_view(self, user: User, organisation: Organisation) -> bool:
        role = self.get_user_role(user, organisation)
        return role in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]

    def can_edit(self, user: User, organisation: Organisation) -> bool:
        if user.is_superuser:
            return True
        role = self.get_user_role(user, organisation)
        return role == ROLE_ADMIN

    def can_create(self, user: User) -> bool:
        return user.is_superuser

    def can_delete(self, user: User, organisation: Organisation) -> bool:
        return user.is_superuser

    def can_manage_members(self, user: User, organisation: Organisation) -> bool:
        role = self.get_user_role(user, organisation)
        return role == ROLE_ADMIN

    @requires_permission("view")
    def get_organisation(self, user: User, organisation: Organisation) -> Organisation:
        """Get organisation if user has permission"""
        return organisation

    def get_user_organisation(self, user: User) -> Optional[Organisation]:
        """Get user's primary organisation"""
        return user.organisation_set.first()

    def get_user_organisation_ids(self, user: User) -> Set[int]:
        """Get IDs of organisations user belongs to"""
        return set(
            OrganisationMembership.objects.filter(user=user).values_list(
                "organisation_id", flat=True
            )
        )

    def get_user_accessible_organisations(
        self, projects: QuerySet[Project], user: User
    ) -> Dict[int, List[Organisation]]:
        """Get organisations user has access to for each project"""
        user_org_ids = self.get_user_organisation_ids(user)
        return {
            project.id: [
                org for org in project.organisations.all() if org.id in user_org_ids
            ]
            for project in projects
        }

    @requires_permission("edit")
    def update_organisation(
        self, user: User, organisation: Organisation, data: Dict
    ) -> Organisation:
        """Update organization with provided data"""
        for key, value in data.items():
            setattr(organisation, key, value)
        organisation.save()
        return organisation

    def create_organisation(
        self, user: User, name: str, description: str = ""
    ) -> Organisation:
        """Create a new organization"""
        if not self.can_create(user):
            raise PermissionDenied("User cannot create organisations")

        org = Organisation.objects.create(name=name, description=description)
        self.add_user_to_organisation(
            user=user, added_by=user, organisation=org, role=ROLE_ADMIN
        )
        return org

    @requires_permission("edit", obj_param="organisation")
    def add_user_to_organisation(
        self,
        user: User,
        added_by: User,
        organisation: Organisation,
        role: Literal["ADMIN", "PROJECT_MANAGER"],
    ) -> OrganisationMembership:
        """Add a user to an organisation with specified role"""
        if role not in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]:
            raise ValueError(
                f"Role must be either {ROLE_ADMIN} or {ROLE_PROJECT_MANAGER}"
            )

        return OrganisationMembership.objects.create(
            user=user, organisation=organisation, role=role, added_by=added_by
        )

    @requires_permission("edit")
    def remove_user_from_organisation(
        self, user: User, organisation: Organisation, removed_user: User
    ) -> None:
        """Remove user from organisation and cleanup permissions"""
        # First revoke all project permissions
        ProjectManagerPermission.objects.filter(
            user=removed_user, project__organisations=organisation
        ).delete()

        # Then remove org membership
        OrganisationMembership.objects.filter(
            user=removed_user, organisation=organisation
        ).delete()

    def get_organisation_projects(
        self, organisation: Organisation, with_metrics: bool = True
    ) -> QuerySet[Project]:
        """Get projects for an organisation with optional metrics"""

        projects = Project.objects.filter(
            projectorganisation__organisation=organisation
        )

        if with_metrics:
            projects = projects.annotate(
                survey_count=Count("survey__id", distinct=True),
                manager_count=Count("projectmanagerpermission", distinct=True),
            )
            
        return projects

    @requires_permission("view")
    def get_organisation_members(
        self, user: User, organisation: Organisation
    ) -> QuerySet[OrganisationMembership]:
        """Get all members of an organisation with their roles"""

        return OrganisationMembership.objects.filter(
            organisation=organisation
        ).select_related("user")
