"""
Test the OrganisationJoinRequest model, in particular its partial unique
constraint: at most one PENDING request per (user, organisation), while
still allowing a decided request to be submitted again.
"""

from django.db import IntegrityError, transaction

import SORT.test.test_case
from home.constants import ROLE_PROJECT_MANAGER
from home.models import OrganisationJoinRequest
from SORT.test.model_factory import (
    OrganisationFactory,
    OrganisationJoinRequestFactory,
    UserFactory,
)


class OrganisationJoinRequestModelTestCase(SORT.test.test_case.SORTTestCase):
    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory()
        self.requester = UserFactory()

    def test_defaults(self):
        join_request = OrganisationJoinRequest.objects.create(
            user=self.requester, organisation=self.organisation
        )

        self.assertEqual(join_request.status, OrganisationJoinRequest.Status.PENDING)
        self.assertTrue(join_request.is_pending)
        self.assertEqual(join_request.message, "")
        self.assertEqual(join_request.granted_role, "")
        self.assertEqual(join_request.decision_note, "")
        self.assertIsNone(join_request.decided_by)
        self.assertIsNone(join_request.decided_at)

    def test_str(self):
        join_request = OrganisationJoinRequestFactory(
            user=self.requester, organisation=self.organisation
        )

        self.assertIn(str(self.requester), str(join_request))
        self.assertIn(self.organisation.name, str(join_request))
        self.assertIn("Pending", str(join_request))

    def test_duplicate_pending_request_is_rejected(self):
        OrganisationJoinRequestFactory(
            user=self.requester, organisation=self.organisation
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OrganisationJoinRequestFactory(
                    user=self.requester, organisation=self.organisation
                )

        self.assertEqual(
            OrganisationJoinRequest.objects.filter(
                user=self.requester, organisation=self.organisation
            ).count(),
            1,
        )

    def test_new_pending_request_allowed_once_previous_one_is_decided(self):
        """The constraint is conditional on PENDING, so a user whose request was
        rejected, withdrawn or approved is not permanently blocked."""
        decided_statuses = (
            OrganisationJoinRequest.Status.REJECTED,
            OrganisationJoinRequest.Status.WITHDRAWN,
            OrganisationJoinRequest.Status.APPROVED,
        )

        for status in decided_statuses:
            with self.subTest(status=status):
                OrganisationJoinRequest.objects.filter(
                    user=self.requester, organisation=self.organisation
                ).delete()
                OrganisationJoinRequestFactory(
                    user=self.requester,
                    organisation=self.organisation,
                    status=status,
                )

                join_request = OrganisationJoinRequestFactory(
                    user=self.requester, organisation=self.organisation
                )

                self.assertTrue(join_request.is_pending)

    def test_pending_requests_for_different_organisations_allowed(self):
        first, second = OrganisationFactory.create_batch(2)

        OrganisationJoinRequestFactory(user=self.requester, organisation=first)
        OrganisationJoinRequestFactory(user=self.requester, organisation=second)

        self.assertEqual(
            OrganisationJoinRequest.objects.filter(user=self.requester).count(), 2
        )

    def test_pending_requests_from_different_users_allowed(self):
        other_requester = UserFactory()

        OrganisationJoinRequestFactory(
            user=self.requester, organisation=self.organisation
        )
        OrganisationJoinRequestFactory(
            user=other_requester, organisation=self.organisation
        )

        self.assertEqual(
            OrganisationJoinRequest.objects.filter(
                organisation=self.organisation
            ).count(),
            2,
        )

    def test_ordering_is_newest_first(self):
        older = OrganisationJoinRequestFactory(
            user=self.requester, organisation=self.organisation
        )
        newer = OrganisationJoinRequestFactory(user=UserFactory())

        self.assertEqual(
            list(OrganisationJoinRequest.objects.all()),
            [newer, older],
        )

    def test_granted_role_accepts_membership_roles(self):
        join_request = OrganisationJoinRequestFactory(
            user=self.requester,
            organisation=self.organisation,
            status=OrganisationJoinRequest.Status.APPROVED,
            granted_role=ROLE_PROJECT_MANAGER,
        )
        join_request.full_clean()

        self.assertFalse(join_request.is_pending)
        self.assertEqual(join_request.granted_role, ROLE_PROJECT_MANAGER)
