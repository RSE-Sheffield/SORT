"""
Test the organisation join request service: permissions, the pending-request
constraint, and the concurrency guards around approving a request.
"""

from django.core.exceptions import PermissionDenied

import SORT.test.test_case
from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from home.models import OrganisationJoinRequest, OrganisationMembership
from home.services import (
    AlreadyMemberError,
    DuplicateJoinRequestError,
    JoinRequestAlreadyDecidedError,
    OrganisationJoinRequestService,
)
from SORT.test.model_factory import (
    OrganisationFactory,
    OrganisationJoinRequestFactory,
    OrganisationMembershipFactory,
    UserFactory,
)


class OrganisationJoinRequestServiceTestCase(SORT.test.test_case.ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.service = OrganisationJoinRequestService()
        self.organisation = OrganisationFactory()
        self.admin_user = self.organisation.members.first()
        self.requester = UserFactory()
        self.project_manager = OrganisationMembershipFactory(
            organisation=self.organisation, role=ROLE_PROJECT_MANAGER
        ).user

    def _pending_request(self):
        return OrganisationJoinRequestFactory(
            user=self.requester, organisation=self.organisation
        )

    # --- create ---------------------------------------------------------------

    def test_create_join_request(self):
        join_request = self.service.create_join_request(
            self.requester, self.organisation, message="  I am a research nurse  "
        )

        self.assertTrue(join_request.is_pending)
        self.assertEqual(join_request.user, self.requester)
        self.assertEqual(join_request.organisation, self.organisation)
        self.assertEqual(join_request.message, "I am a research nurse")

    def test_create_join_request_without_message(self):
        join_request = self.service.create_join_request(
            self.requester, self.organisation
        )

        self.assertEqual(join_request.message, "")

    def test_create_join_request_rejected_for_existing_member(self):
        with self.assertRaises(AlreadyMemberError):
            self.service.create_join_request(self.admin_user, self.organisation)

        self.assertFalse(OrganisationJoinRequest.objects.exists())

    def test_create_duplicate_join_request_rejected(self):
        self._pending_request()

        with self.assertRaises(DuplicateJoinRequestError):
            self.service.create_join_request(self.requester, self.organisation)

        # The service must use a savepoint around the insert, otherwise the
        # IntegrityError would leave the surrounding transaction unusable and
        # this query would raise TransactionManagementError.
        self.assertEqual(OrganisationJoinRequest.objects.count(), 1)

    def test_create_join_request_after_rejection(self):
        join_request = self._pending_request()
        self.service.reject(self.admin_user, join_request)

        new_request = self.service.create_join_request(
            self.requester, self.organisation
        )

        self.assertTrue(new_request.is_pending)
        self.assertEqual(OrganisationJoinRequest.objects.count(), 2)

    def test_create_join_request_for_other_organisation_allowed(self):
        other_organisation = OrganisationFactory()
        self._pending_request()

        join_request = self.service.create_join_request(
            self.requester, other_organisation
        )

        self.assertEqual(join_request.organisation, other_organisation)

    def test_staff_user_may_request_to_join(self):
        """A staff account has no membership but Organisation.get_user_role
        reports ADMIN for it, so can_create must not be based on that."""
        staff_user = UserFactory(is_staff=True)

        join_request = self.service.create_join_request(staff_user, self.organisation)

        self.assertTrue(join_request.is_pending)

    # --- approve --------------------------------------------------------------

    def test_approve_grants_project_manager_by_default(self):
        join_request = self._pending_request()

        membership = self.service.approve(self.admin_user, join_request)

        self.assertEqual(membership.user, self.requester)
        self.assertEqual(membership.organisation, self.organisation)
        self.assertEqual(membership.role, ROLE_PROJECT_MANAGER)
        self.assertEqual(membership.added_by, self.admin_user)

        join_request.refresh_from_db()
        self.assertEqual(
            join_request.status, OrganisationJoinRequest.Status.APPROVED
        )
        self.assertEqual(join_request.granted_role, ROLE_PROJECT_MANAGER)
        self.assertEqual(join_request.decided_by, self.admin_user)
        self.assertIsNotNone(join_request.decided_at)

    def test_approve_with_admin_role(self):
        join_request = self._pending_request()

        membership = self.service.approve(
            self.admin_user, join_request, role=ROLE_ADMIN
        )

        self.assertEqual(membership.role, ROLE_ADMIN)
        join_request.refresh_from_db()
        self.assertEqual(join_request.granted_role, ROLE_ADMIN)

    def test_approve_with_invalid_role(self):
        join_request = self._pending_request()

        with self.assertRaises(ValueError):
            self.service.approve(self.admin_user, join_request, role="OWNER")

        join_request.refresh_from_db()
        self.assertTrue(join_request.is_pending)

    def test_approve_by_superuser(self):
        join_request = self._pending_request()

        membership = self.service.approve(self.superuser, join_request)

        self.assertEqual(membership.user, self.requester)

    def test_approve_by_project_manager_denied(self):
        join_request = self._pending_request()

        with self.assertRaises(PermissionDenied):
            self.service.approve(self.project_manager, join_request)

        self.assertFalse(
            OrganisationMembership.objects.filter(
                user=self.requester, organisation=self.organisation
            ).exists()
        )
        join_request.refresh_from_db()
        self.assertTrue(join_request.is_pending)

    def test_approve_by_non_member_denied(self):
        join_request = self._pending_request()
        outsider = UserFactory()

        with self.assertRaises(PermissionDenied):
            self.service.approve(outsider, join_request)

    def test_approve_twice_raises_and_creates_one_membership(self):
        join_request = self._pending_request()
        self.service.approve(self.admin_user, join_request)

        with self.assertRaises(JoinRequestAlreadyDecidedError):
            self.service.approve(self.admin_user, join_request)

        self.assertEqual(
            OrganisationMembership.objects.filter(
                user=self.requester, organisation=self.organisation
            ).count(),
            1,
        )

    def test_approve_when_user_was_added_manually_meanwhile(self):
        """An admin may add the requester through the invite flow while their
        request sits pending; approving must then be a no-op on membership
        rather than tripping OrganisationMembership's unique_together."""
        join_request = self._pending_request()
        existing = OrganisationMembershipFactory(
            user=self.requester,
            organisation=self.organisation,
            role=ROLE_ADMIN,
        )

        membership = self.service.approve(
            self.admin_user, join_request, role=ROLE_PROJECT_MANAGER
        )

        self.assertEqual(membership.pk, existing.pk)
        self.assertEqual(membership.role, ROLE_ADMIN)
        self.assertEqual(
            OrganisationMembership.objects.filter(
                user=self.requester, organisation=self.organisation
            ).count(),
            1,
        )
        join_request.refresh_from_db()
        self.assertEqual(
            join_request.status, OrganisationJoinRequest.Status.APPROVED
        )
        self.assertEqual(join_request.granted_role, ROLE_ADMIN)

    # --- reject ---------------------------------------------------------------

    def test_reject(self):
        join_request = self._pending_request()

        self.service.reject(self.admin_user, join_request, note="  Not our trust  ")

        join_request.refresh_from_db()
        self.assertEqual(
            join_request.status, OrganisationJoinRequest.Status.REJECTED
        )
        self.assertEqual(join_request.decision_note, "Not our trust")
        self.assertEqual(join_request.decided_by, self.admin_user)
        self.assertIsNotNone(join_request.decided_at)
        self.assertFalse(
            OrganisationMembership.objects.filter(
                user=self.requester, organisation=self.organisation
            ).exists()
        )

    def test_reject_by_project_manager_denied(self):
        join_request = self._pending_request()

        with self.assertRaises(PermissionDenied):
            self.service.reject(self.project_manager, join_request)

    def test_reject_already_decided(self):
        join_request = self._pending_request()
        self.service.reject(self.admin_user, join_request)

        with self.assertRaises(JoinRequestAlreadyDecidedError):
            self.service.reject(self.admin_user, join_request)

    # --- withdraw -------------------------------------------------------------

    def test_withdraw_by_requester(self):
        join_request = self._pending_request()

        self.service.withdraw(self.requester, join_request)

        join_request.refresh_from_db()
        self.assertEqual(
            join_request.status, OrganisationJoinRequest.Status.WITHDRAWN
        )
        self.assertEqual(join_request.decided_by, self.requester)

    def test_withdraw_by_other_user_denied(self):
        join_request = self._pending_request()

        with self.assertRaises(PermissionDenied):
            self.service.withdraw(self.admin_user, join_request)

    def test_withdraw_already_decided(self):
        join_request = self._pending_request()
        self.service.withdraw(self.requester, join_request)

        with self.assertRaises(JoinRequestAlreadyDecidedError):
            self.service.withdraw(self.requester, join_request)

    # --- queries --------------------------------------------------------------

    def test_get_requests_returns_pending_by_default(self):
        pending = self._pending_request()
        OrganisationJoinRequestFactory(
            organisation=self.organisation,
            status=OrganisationJoinRequest.Status.REJECTED,
        )

        requests = self.service.get_requests(self.admin_user, self.organisation)

        self.assertEqual(list(requests), [pending])

    def test_get_requests_with_full_history(self):
        self._pending_request()
        OrganisationJoinRequestFactory(
            organisation=self.organisation,
            status=OrganisationJoinRequest.Status.REJECTED,
        )

        requests = self.service.get_requests(
            self.admin_user, self.organisation, status=None
        )

        self.assertEqual(requests.count(), 2)

    def test_get_requests_excludes_other_organisations(self):
        self._pending_request()
        OrganisationJoinRequestFactory()

        requests = self.service.get_requests(self.admin_user, self.organisation)

        self.assertEqual(requests.count(), 1)

    def test_get_requests_denied_for_project_manager(self):
        with self.assertRaises(PermissionDenied):
            self.service.get_requests(self.project_manager, self.organisation)

    def test_get_user_requests(self):
        own = self._pending_request()
        OrganisationJoinRequestFactory()

        self.assertEqual(list(self.service.get_user_requests(self.requester)), [own])

    def test_get_pending_organisation_ids(self):
        other_organisation = OrganisationFactory()
        self._pending_request()
        OrganisationJoinRequestFactory(
            user=self.requester,
            organisation=other_organisation,
            status=OrganisationJoinRequest.Status.REJECTED,
        )

        self.assertEqual(
            self.service.get_pending_organisation_ids(self.requester),
            {self.organisation.pk},
        )

    def test_get_pending_count(self):
        self._pending_request()
        OrganisationJoinRequestFactory(organisation=self.organisation)
        OrganisationJoinRequestFactory(
            organisation=self.organisation,
            status=OrganisationJoinRequest.Status.APPROVED,
        )

        self.assertEqual(
            self.service.get_pending_count(self.admin_user, self.organisation), 2
        )

    def test_get_pending_count_is_zero_for_non_admin(self):
        self._pending_request()

        self.assertEqual(
            self.service.get_pending_count(self.project_manager, self.organisation), 0
        )
        self.assertEqual(self.service.get_pending_count(self.admin_user, None), 0)

    # --- permission predicates ------------------------------------------------

    def test_can_view(self):
        join_request = self._pending_request()

        self.assertTrue(self.service.can_view(self.requester, join_request))
        self.assertTrue(self.service.can_view(self.admin_user, join_request))
        self.assertFalse(self.service.can_view(self.project_manager, join_request))
        self.assertFalse(self.service.can_view(UserFactory(), join_request))

    def test_can_create_for_any_authenticated_user(self):
        """Existing membership is validation, reported by create_join_request as
        AlreadyMemberError, so it must not be folded into can_create — see
        test_create_join_request_rejected_for_existing_member."""
        self.assertTrue(self.service.can_create(self.requester, self.organisation))
        self.assertTrue(self.service.can_create(self.admin_user, self.organisation))
