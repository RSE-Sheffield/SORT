"""
Organisation join request service with integrated permissions.

Users request to join an existing organisation and an organisation ADMIN
approves (granting a role of their choosing) or rejects the request.

This is a separate service from ``OrganisationService`` for a mechanical
reason: ``requires_permission`` resolves ``can_<type>(user, obj)`` on the
service instance, and ``OrganisationService.can_edit`` already means "may edit
this *Organisation*". The methods here need ``can_edit(user, join_request)``.
Keeping them apart gives each service one coherent permission-object type.
Permission *logic* is not duplicated — the predicates below delegate to
``organisation_service.can_manage_members``, so "who may decide a join request"
stays defined in one place.

No ``DataProtectionEvent`` is recorded when a request is decided.
``DataProtectionEvent.EventType`` is deliberately scoped to data protection
actions taken on a subject's personal data (erasure, export, restriction,
consent withdrawal, membership removal). Granting access is already audited
in-domain: ``OrganisationJoinRequest`` stores ``decided_by``, ``decided_at``
and ``granted_role``, and the resulting ``OrganisationMembership`` stores
``added_by``. Adding a "membership added" event type would widen the meaning of
the append-only log and change the staff console's log page, so it should be a
deliberate decision of its own rather than a side effect of this feature.
"""

from typing import Optional, Set

from django.db import IntegrityError, transaction
from django.db.models.query import QuerySet
from django.utils import timezone

from ..constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from ..models import (
    Organisation,
    OrganisationJoinRequest,
    OrganisationMembership,
    User,
)
from .base import BasePermissionService, requires_permission
from .organisation import organisation_service


class JoinRequestError(Exception):
    """Base class for join request errors that views should report to the user
    rather than let surface as a 500."""


class AlreadyMemberError(JoinRequestError):
    """The requester already belongs to the organisation."""


class DuplicateJoinRequestError(JoinRequestError):
    """The requester already has a pending request for this organisation."""


class JoinRequestAlreadyDecidedError(JoinRequestError):
    """The request was approved, rejected or withdrawn by someone else first."""


class OrganisationJoinRequestService(BasePermissionService):
    """Service for managing self-service organisation join requests."""

    # --- permission predicates -------------------------------------------------

    def can_create(self, user: User, organisation: Organisation) -> bool:
        """Any authenticated user may request to join any organisation.

        Deliberately does *not* check for existing membership. Already being a
        member is validation, not a permission problem, and folding it in here
        would mean ``requires_permission`` raised an opaque PermissionDenied
        before ``create_join_request`` could raise the specific
        AlreadyMemberError that views report to the user.

        Note this must not be based on ``organisation_service.can_view`` either:
        ``Organisation.get_user_role`` reports ROLE_ADMIN for any staff or
        superuser account regardless of membership, which would wrongly stop
        those users from ever requesting to join an organisation.
        """
        return bool(user and user.is_authenticated)

    def can_view(self, user: User, join_request: OrganisationJoinRequest) -> bool:
        """The requester, or anyone who may manage the organisation's members."""
        if not user or not user.is_authenticated:
            return False
        if join_request.user_id == user.pk:
            return True
        return organisation_service.can_manage_members(
            user, join_request.organisation
        )

    def can_edit(self, user: User, join_request: OrganisationJoinRequest) -> bool:
        """Deciding a request (approve/reject) is member management."""
        return organisation_service.can_manage_members(user, join_request.organisation)

    def can_delete(self, user: User, join_request: OrganisationJoinRequest) -> bool:
        """Only the requester may withdraw their own request."""
        if not user or not user.is_authenticated:
            return False
        return join_request.user_id == user.pk or user.is_superuser

    def can_manage_members(self, user: User, organisation: Organisation) -> bool:
        """Delegate to OrganisationService.

        Defined here so ``@requires_permission("manage_members", ...)`` resolves
        via ``getattr`` on this service.
        """
        return organisation_service.can_manage_members(user, organisation)

    # --- commands --------------------------------------------------------------

    @requires_permission("create", obj_param="organisation")
    def create_join_request(
        self, user: User, organisation: Organisation, message: str = ""
    ) -> OrganisationJoinRequest:
        """
        Submit a request for `user` to join `organisation`.

        @param user: the user asking to join
        @param organisation: the organisation they want to join
        @param message: optional note shown to the organisation's administrators
        """
        if OrganisationMembership.objects.filter(
            user=user, organisation=organisation
        ).exists():
            raise AlreadyMemberError(
                f"User '{user}' is already a member of '{organisation}'"
            )

        try:
            # The savepoint is required, not cosmetic: catching IntegrityError
            # without one leaves the surrounding transaction unusable (every
            # later query would raise TransactionManagementError), and both
            # request handling and Django's TestCase run inside a transaction.
            with transaction.atomic():
                return OrganisationJoinRequest.objects.create(
                    user=user,
                    organisation=organisation,
                    message=(message or "").strip(),
                )
        except IntegrityError as exc:
            # Violates the partial unique constraint, i.e. a pending request
            # already exists. The constraint is the only race-safe guard, so
            # there is no point pre-checking with a query.
            raise DuplicateJoinRequestError(
                f"User '{user}' already has a pending request to join '{organisation}'"
            ) from exc

    @requires_permission("edit", obj_param="join_request")
    def approve(
        self,
        user: User,
        join_request: OrganisationJoinRequest,
        role: str = ROLE_PROJECT_MANAGER,
    ) -> OrganisationMembership:
        """
        Approve `join_request`, adding the requester to the organisation.

        @param user: the administrator approving the request
        @param join_request: the request to approve
        @param role: the role to grant the requester
        @return: the requester's organisation membership
        """
        if role not in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]:
            raise ValueError(
                f"Role must be either {ROLE_ADMIN} or {ROLE_PROJECT_MANAGER}"
            )

        with transaction.atomic():
            # Re-read under a row lock so two administrators clicking Approve at
            # the same time cannot both create a membership: the loser sees a
            # non-pending status below. (SQLite does not emit FOR UPDATE, so the
            # in-transaction status re-check is what actually guarantees this.)
            locked_request = self._lock(join_request)

            membership = OrganisationMembership.objects.filter(
                user=locked_request.user, organisation=locked_request.organisation
            ).first()
            if membership is None:
                # Keyword arguments are required here: add_user_to_organisation
                # is decorated with obj_param="organisation" but takes
                # organisation as its third parameter, so a positional call
                # would have the decorator permission-check `user_to_add`.
                membership = organisation_service.add_user_to_organisation(
                    user=user,
                    user_to_add=locked_request.user,
                    organisation=locked_request.organisation,
                    role=role,
                )

            locked_request.status = OrganisationJoinRequest.Status.APPROVED
            locked_request.granted_role = membership.role
            locked_request.decided_by = user
            locked_request.decided_at = timezone.now()
            locked_request.save(
                update_fields=["status", "granted_role", "decided_by", "decided_at"]
            )

        join_request.refresh_from_db()
        return membership

    @requires_permission("edit", obj_param="join_request")
    def reject(
        self, user: User, join_request: OrganisationJoinRequest, note: str = ""
    ) -> OrganisationJoinRequest:
        """
        Reject `join_request`. The requester may submit a new request later.

        @param user: the administrator rejecting the request
        @param join_request: the request to reject
        @param note: optional reason, included in the email to the requester
        """
        with transaction.atomic():
            locked_request = self._lock(join_request)
            locked_request.status = OrganisationJoinRequest.Status.REJECTED
            locked_request.decision_note = (note or "").strip()
            locked_request.decided_by = user
            locked_request.decided_at = timezone.now()
            locked_request.save(
                update_fields=["status", "decision_note", "decided_by", "decided_at"]
            )

        join_request.refresh_from_db()
        return join_request

    @requires_permission("delete", obj_param="join_request")
    def withdraw(
        self, user: User, join_request: OrganisationJoinRequest
    ) -> OrganisationJoinRequest:
        """
        Withdraw `join_request` on the requester's own behalf, freeing them to
        request a different organisation (or the same one again).
        """
        with transaction.atomic():
            locked_request = self._lock(join_request)
            locked_request.status = OrganisationJoinRequest.Status.WITHDRAWN
            locked_request.decided_by = user
            locked_request.decided_at = timezone.now()
            locked_request.save(
                update_fields=["status", "decided_by", "decided_at"]
            )

        join_request.refresh_from_db()
        return join_request

    # --- queries ---------------------------------------------------------------

    @requires_permission("manage_members", obj_param="organisation")
    def get_requests(
        self,
        user: User,
        organisation: Organisation,
        status: Optional[str] = OrganisationJoinRequest.Status.PENDING,
    ) -> QuerySet[OrganisationJoinRequest]:
        """
        Join requests for `organisation`, for its administrators to review.

        @param status: filter to this status, or pass None for the full history
        """
        queryset = OrganisationJoinRequest.objects.filter(
            organisation=organisation
        ).select_related("user", "decided_by")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_user_requests(self, user: User) -> QuerySet[OrganisationJoinRequest]:
        """All of `user`'s own requests, whatever their status."""
        if not user or not user.is_authenticated:
            return OrganisationJoinRequest.objects.none()
        return OrganisationJoinRequest.objects.filter(user=user).select_related(
            "organisation"
        )

    def get_pending_organisation_ids(self, user: User) -> Set[int]:
        """IDs of organisations `user` has an outstanding request for, so the
        browse page can show 'Pending' instead of a request button."""
        if not user or not user.is_authenticated:
            return set()
        return set(
            OrganisationJoinRequest.objects.filter(
                user=user, status=OrganisationJoinRequest.Status.PENDING
            ).values_list("organisation_id", flat=True)
        )

    def get_pending_count(self, user: User, organisation: Organisation) -> int:
        """Number of requests awaiting a decision, for the navigation badge.

        Returns 0 rather than raising for users who may not manage members, so
        callers rendering shared page furniture do not need to guard.
        """
        if not organisation or not self.can_manage_members(user, organisation):
            return 0
        return OrganisationJoinRequest.objects.filter(
            organisation=organisation, status=OrganisationJoinRequest.Status.PENDING
        ).count()

    # --- internals -------------------------------------------------------------

    @staticmethod
    def _lock(join_request: OrganisationJoinRequest) -> OrganisationJoinRequest:
        """Re-read `join_request` under a row lock, asserting it is still
        pending. Must be called inside a transaction."""
        locked_request = (
            OrganisationJoinRequest.objects.select_for_update()
            .select_related("user", "organisation")
            .get(pk=join_request.pk)
        )
        if not locked_request.is_pending:
            raise JoinRequestAlreadyDecidedError(
                f"Join request {join_request.pk} is already "
                f"{locked_request.get_status_display().lower()}"
            )
        return locked_request


organisation_join_request_service = OrganisationJoinRequestService()
