"""
Organisation service with integrated permissions
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.db.models.query import QuerySet
from django.http import HttpRequest

from ..constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from ..models import (
    DataProtectionEvent,
    Organisation,
    OrganisationMembership,
    Project,
    User,
)
from .base import BasePermissionService, requires_permission
from .data_protection import data_protection_service


def remove_membership_and_record_event(
    membership_qs: QuerySet[OrganisationMembership],
    *,
    actioned_by: User,
    notes: str,
) -> None:
    """
    Delete the membership matched by membership_qs and record its
    MEMBERSHIP_REMOVED audit event as one atomic, lock-serialized unit.

    UK GDPR Art. 5(2) accountability: the removal and its audit record are a
    single atomic unit so a failed audit write rolls back the deletion — a
    removal can never persist unaudited.

    membership_qs must resolve to at most one row. select_for_update()
    serializes concurrent removals of the same membership: only the first
    caller succeeds, later callers raise OrganisationMembership.DoesNotExist
    instead of recording a duplicate event.
    """
    with transaction.atomic():
        membership = membership_qs.select_for_update().get()
        subject_user = membership.user
        membership.delete()
        data_protection_service.record_event(
            event_type=DataProtectionEvent.EventType.MEMBERSHIP_REMOVED,
            subject_user=subject_user,
            actioned_by=actioned_by,
            notes=notes,
        )


@dataclass(frozen=True)
class OrganisationMergePlan:
    """
    What merging `source` into `target` would do, computed up front so a
    dry-run report and the real merge share one source of truth.
    """

    source: Organisation
    target: Organisation
    projects: List[Project]
    memberships_to_move: List[OrganisationMembership]
    memberships_to_drop: List[OrganisationMembership]

    def describe(self) -> str:
        lines = [
            f"Merge '{self.source.name}' (id={self.source.pk}) into "
            f"'{self.target.name}' (id={self.target.pk})",
            f"  Projects to move: {len(self.projects)}",
            *(f"    - {p.name} (id={p.pk})" for p in self.projects),
            f"  Memberships to transfer: {len(self.memberships_to_move)}",
            *(f"    - {m.user.email} as {m.role}" for m in self.memberships_to_move),
            f"  Duplicate memberships to drop (keeping target's role): "
            f"{len(self.memberships_to_drop)}",
            *(
                f"    - {m.user.email} (was {m.role} in source)"
                for m in self.memberships_to_drop
            ),
            f"  '{self.source.name}' will be deleted after the merge.",
        ]
        return "\n".join(lines)


def plan_organisation_merge(
    source: Organisation, target: Organisation
) -> OrganisationMergePlan:
    """
    Read-only: work out which projects and memberships a merge of `source`
    into `target` would move, and which duplicate memberships it would drop.
    """
    if source.pk == target.pk:
        raise ValueError("Cannot merge an organisation into itself")

    target_user_ids = set(
        OrganisationMembership.objects.filter(organisation=target).values_list(
            "user_id", flat=True
        )
    )
    source_memberships = list(
        OrganisationMembership.objects.filter(organisation=source).select_related(
            "user"
        )
    )
    memberships_to_drop = [
        m for m in source_memberships if m.user_id in target_user_ids
    ]
    memberships_to_move = [
        m for m in source_memberships if m.user_id not in target_user_ids
    ]
    projects = list(Project.objects.filter(organisation=source))

    return OrganisationMergePlan(
        source, target, projects, memberships_to_move, memberships_to_drop
    )


class OrganisationService(BasePermissionService):
    """Service for managing organisations with integrated permissions"""

    def get_user_role(self, user: User, organisation: Organisation) -> Optional[str]:
        try:
            membership = organisation.organisationmembership_set.filter(
                user=user
            ).first()
            return membership.role if membership else None
        except AttributeError:  # In case user is AnonymousUser
            return None

    def can_view(self, user: User, organisation: Organisation) -> bool:
        role = self.get_user_role(user, organisation)
        return role in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]

    def can_edit(self, user: User, organisation: Organisation) -> bool:
        if user.is_superuser:
            return True
        role = self.get_user_role(user, organisation)
        return role == ROLE_ADMIN

    def can_create_organisation(self, user: User) -> bool:
        """Anyone with a login can create an organisation, including users
        who already belong to one or more organisations."""
        return bool(user and user.is_authenticated)

    def can_delete(self, user: User, organisation: Organisation) -> bool:
        if user.is_superuser:
            return True
        role = self.get_user_role(user, organisation)
        return role == ROLE_ADMIN

    def can_manage_members(self, user: User, organisation: Organisation) -> bool:
        if user.is_superuser:
            return True
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

    def get_active_organisation(self, request: HttpRequest) -> Optional[Organisation]:
        """
        Resolve the organisation the user is currently "in", for users who may
        belong to more than one. The choice is sticky across requests via
        ``request.session["active_organisation_id"]``.

        Fallback chain: no memberships -> None; exactly one membership -> that
        organisation (so single-org users see no behaviour change); a valid
        session choice -> that organisation; otherwise (no session choice yet,
        or the previously active organisation was left/removed) -> the
        earliest-joined membership, and the session is brought back in sync.
        """
        user = request.user
        if not user or not user.is_authenticated:
            return None

        memberships = list(
            OrganisationMembership.objects.filter(user=user)
            .select_related("organisation")
            .order_by("joined_at")
        )
        if not memberships:
            request.session.pop("active_organisation_id", None)
            return None

        if len(memberships) == 1:
            organisation = memberships[0].organisation
            request.session["active_organisation_id"] = organisation.id
            return organisation

        active_id = request.session.get("active_organisation_id")
        for membership in memberships:
            if membership.organisation_id == active_id:
                return membership.organisation

        organisation = memberships[0].organisation
        request.session["active_organisation_id"] = organisation.id
        return organisation

    def set_active_organisation(
        self, request: HttpRequest, organisation: Organisation
    ) -> None:
        """
        Switch the session's active organisation. Caller must have already
        verified the user is a member of ``organisation``.
        """
        request.session["active_organisation_id"] = organisation.id

    def get_user_organisations(self, user: User) -> QuerySet[Organisation]:
        """All organisations `user` belongs to, for switcher UI."""
        return Organisation.objects.filter(members=user).order_by("name")

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
        self, user: User, name: str, description: str = None
    ) -> Organisation:
        """
        Create a new organisation, and add the creator to it.
        Anyone who has a login should be able to create an organisation
        """

        org = Organisation.objects.create(name=name, description=description or "")
        OrganisationMembership.objects.create(
            user=user, organisation=org, role=ROLE_ADMIN, added_by=user
        )
        return org

    @requires_permission("edit", obj_param="organisation")
    def add_user_to_organisation(
        self,
        user: User,
        user_to_add: User,
        organisation: Organisation,
        role: str,
    ) -> OrganisationMembership:
        """
        Add a user to an organisation with specified role

        @param user: user who is adding the user to the organisation
        @param user_to_add: user to add
        @param organisation: The organisation to add the user to
        @param role: The role that the user has in the organisation
        """
        if role not in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]:
            raise ValueError(
                f"Role must be either {ROLE_ADMIN} or {ROLE_PROJECT_MANAGER}"
            )

        return OrganisationMembership.objects.create(
            user=user_to_add, organisation=organisation, role=role, added_by=user
        )

    @requires_permission("edit", obj_param="organisation")
    def remove_user_from_organisation(
        self, user: User, organisation: Organisation, removed_user: User
    ) -> None:
        """
        Remove a user from organisation

        @param user: The organisation manager/admin
        @param organisation: The organisation to remove the user from
        @param removed_user: The user to revoke permissions from
        """
        if not self.can_edit(user, organisation):
            raise PermissionError(
                f"User '{user}' does not have permission to remove users from organisation '{organisation}'"
            )

        remove_membership_and_record_event(
            OrganisationMembership.objects.filter(
                user=removed_user, organisation=organisation
            ),
            actioned_by=user,
            notes=f"Removed from organisation '{organisation.name}'",
        )

    def get_organisation_projects(
        self, organisation: Organisation, user: User = None, with_metrics: bool = True
    ) -> QuerySet[Project]:
        """Get projects for an organisation with optional metrics"""
        if not self.can_view(user, organisation):
            return Project.objects.none()

        base_query = Project.objects.filter(organisation=organisation)

        # Add metrics
        if with_metrics:
            base_query = base_query.annotate(
                survey_count=Count("survey__id", distinct=True),
            ).select_related("created_by", "organisation")

        return base_query.order_by("-created_at")

    @requires_permission("view", obj_param="organisation")
    def get_organisation_members(
        self, user: User, organisation: Organisation
    ) -> QuerySet[OrganisationMembership]:
        """Get all members of an organisation with their roles"""
        return OrganisationMembership.objects.filter(
            organisation=organisation
        ).select_related("user")

    def can_merge(self, user: User) -> bool:
        """
        Merging spans two organisations, so this is a staff-level action
        rather than something scoped to a role within either org.
        """
        return bool(
            user and user.is_authenticated and (user.is_staff or user.is_superuser)
        )

    def merge_organisations(
        self, user: User, source: Organisation, target: Organisation
    ) -> OrganisationMergePlan:
        """
        Move source's projects and memberships into target, then delete
        source. Where a user belongs to both orgs, target's existing role
        wins and the duplicate source membership is dropped.

        Atomic: the plan is computed once and applied as a single unit, so a
        failure partway through (e.g. the audit write) rolls back every
        reassignment and the source org is never left half-merged.
        """
        if not self.can_merge(user):
            raise PermissionDenied(
                f"User '{user}' does not have permission to merge organisations"
            )

        plan = plan_organisation_merge(source, target)

        with transaction.atomic():
            for membership in plan.memberships_to_drop:
                remove_membership_and_record_event(
                    OrganisationMembership.objects.filter(pk=membership.pk),
                    actioned_by=user,
                    notes=(
                        f"Duplicate membership in '{source.name}' removed: "
                        f"already a member of '{target.name}' during "
                        f"organisation merge"
                    ),
                )

            OrganisationMembership.objects.filter(
                pk__in=[m.pk for m in plan.memberships_to_move]
            ).update(organisation=target)

            Project.objects.filter(organisation=source).update(organisation=target)

            data_protection_service.record_event(
                event_type=DataProtectionEvent.EventType.ORGANISATION_MERGED,
                subject_user=user,
                actioned_by=user,
                notes=(
                    f"Merged organisation '{source.name}' (id={source.pk}) into "
                    f"'{target.name}' (id={target.pk}): {len(plan.projects)} "
                    f"project(s) moved, {len(plan.memberships_to_move)} "
                    f"membership(s) transferred, {len(plan.memberships_to_drop)} "
                    f"duplicate membership(s) removed."
                ),
            )

            source.delete()

        return plan


organisation_service = OrganisationService()
