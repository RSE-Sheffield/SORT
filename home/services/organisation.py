"""
Organisation service with integrated permissions
"""
from typing import Dict, Optional, Set
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.db.models.query import QuerySet

from ..constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from ..models import (
    Organisation,
    OrganisationMembership,
    Project,
    User
)
from .base import BasePermissionService, requires_permission


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

    @requires_permission("view", obj_param="organisation")
    def get_organisation(self, user: User, organisation: Organisation) -> Organisation:
        """Get organisation if user has permission"""
        return organisation

    def get_user_organisation(self, user: User) -> Optional[Organisation]:
        """Get user's primary organisation"""
        if not user or not user.is_authenticated:
            return None

        return user.organisation_set.first()

    def get_user_organisation_ids(self, user: User) -> Set[int]:
        """Get IDs of organisations user belongs to"""
        return set(
            OrganisationMembership.objects.filter(user=user).values_list(
                "organisation_id", flat=True
            )
        )

    @requires_permission("edit", obj_param="organisation")
    def update_organisation(
        self, user: User, organisation: Organisation, data: Dict
    ) -> Organisation:
        """Update organisation with provided data"""
        for key, value in data.items():
            setattr(organisation, key, value)
        organisation.save()
        return organisation

    def create_organisation(
        self, user: User, name: str, description: str = ""
    ) -> Organisation:
        """Create a new organisation"""
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
        role: str,
    ) -> OrganisationMembership:
        """Add a user to an organisation with specified role"""
        if role not in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]:
            raise ValueError(
                f"Role must be either {ROLE_ADMIN} or {ROLE_PROJECT_MANAGER}"
            )

        return OrganisationMembership.objects.create(
            user=user, organisation=organisation, role=role, added_by=added_by
        )

    @requires_permission("edit", obj_param="organisation")
    def remove_user_from_organisation(
        self, user: User, organisation: Organisation, removed_user: User
    ) -> None:
        """Remove user from organisation"""
        OrganisationMembership.objects.filter(
            user=removed_user, organisation=organisation
        ).delete()

    def get_organisation_projects(
        self, organisation: Organisation, user: User = None, with_metrics: bool = True
    ) -> QuerySet[Project]:
        """Get projects for an organisation with optional metrics"""
        if not self.can_view(user, organisation):
            return Project.objects.none()

        base_query = Project.objects.filter(organisation=organisation)

        # Add metrics
        if with_metrics:
            projects = base_query.annotate(
                survey_count=Count("survey__id", distinct=True),
            ).select_related("created_by", "organisation")

        return base_query.order_by("-created_on")

    @requires_permission("view", obj_param="organisation")
    def get_organisation_members(
        self, user: User, organisation: Organisation
    ) -> QuerySet[OrganisationMembership]:
        """Get all members of an organisation with their roles"""
        return OrganisationMembership.objects.filter(
            organisation=organisation
        ).select_related("user")
