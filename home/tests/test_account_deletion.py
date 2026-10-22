from http import HTTPStatus
from unittest import mock

from django.core import mail

import SORT.test.test_case
from SORT.test.model_factory import UserFactory
from SORT.test.model_factory.user.constants import PASSWORD

from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from home.models import DataProtectionEvent, ErasureRequest, Organisation, OrganisationMembership
from home.services import organisation_service
from home.services.data_protection import pseudonymise_identifier


class AccountDeletionViewTestCase(SORT.test.test_case.ViewTestCase):
    def login_as(self, user):
        self.assertTrue(
            self.client.login(username=user.email, password=PASSWORD),
            "Authentication failed",
        )

    def test_get_shows_confirmation(self):
        self.login()
        response = self.client.get("/profile/delete/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirects_anonymous(self):
        response = self.client.get("/profile/delete/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_erases_immediately_for_user_with_no_sole_admin_org(self):
        """A user who isn't the sole admin of any org is erased straight away and logged out."""
        target = UserFactory()
        self.login_as(target)

        response = self.client.post("/profile/delete/")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        target.refresh_from_db()
        self.assertFalse(target.is_active)
        self.assertEqual(target.first_name, "Deleted")
        self.assertTrue(target.email.startswith("deleted-"))
        self.assertFalse(target.has_usable_password())

        event = DataProtectionEvent.objects.get(event_type=DataProtectionEvent.EventType.ERASURE)
        self.assertEqual(event.requested_by, target)
        self.assertEqual(event.actioned_by, target)

        # Session has been flushed by the erasure logout.
        follow_up = self.client.get("/profile/")
        self.assertEqual(follow_up.status_code, HTTPStatus.FOUND)

    def test_post_erases_immediately_when_sole_admin_has_no_other_members(self):
        """Being the only member of your own org doesn't block erasure — nobody else is affected."""
        target = UserFactory()
        org = Organisation.objects.create(name="Solo Org")
        OrganisationMembership.objects.create(user=target, organisation=org, role=ROLE_ADMIN)
        self.login_as(target)

        self.client.post("/profile/delete/")

        target.refresh_from_db()
        self.assertFalse(target.is_active)
        self.assertFalse(OrganisationMembership.objects.filter(user=target).exists())

    def test_post_defers_to_staff_when_sole_admin_with_other_members(self):
        """Erasing the only admin of an org that has other members would strand it."""
        target = UserFactory()
        other_member = UserFactory()
        org = Organisation.objects.create(name="Shared Org")
        OrganisationMembership.objects.create(user=target, organisation=org, role=ROLE_ADMIN)
        OrganisationMembership.objects.create(
            user=other_member, organisation=org, role=ROLE_PROJECT_MANAGER
        )
        self.login_as(target)

        response = self.client.post("/profile/delete/")

        self.assertRedirects(response, "/profile/")
        target.refresh_from_db()
        self.assertTrue(target.is_active)
        self.assertTrue(target.has_usable_password())
        self.assertFalse(
            DataProtectionEvent.objects.filter(event_type=DataProtectionEvent.EventType.ERASURE).exists()
        )

        erasure_request = ErasureRequest.objects.get(user=target)
        self.assertEqual(erasure_request.status, ErasureRequest.Status.PENDING)

    def test_post_not_blocked_by_org_with_another_admin(self):
        """A co-admin covering the org means erasure can still happen immediately."""
        target = UserFactory()
        co_admin = UserFactory()
        org = Organisation.objects.create(name="Co-managed Org")
        OrganisationMembership.objects.create(user=target, organisation=org, role=ROLE_ADMIN)
        OrganisationMembership.objects.create(user=co_admin, organisation=org, role=ROLE_ADMIN)
        self.login_as(target)

        self.client.post("/profile/delete/")

        target.refresh_from_db()
        self.assertFalse(target.is_active)

    def test_erasure_event_pseudonymises_original_email(self):
        """The ERASURE pseudonym must match the subject's earlier events, not the placeholder email."""
        target = UserFactory()
        original_email = target.email
        self.login_as(target)

        self.client.post("/profile/delete/")

        event = DataProtectionEvent.objects.get(event_type=DataProtectionEvent.EventType.ERASURE)
        self.assertEqual(event.subject_identifier, pseudonymise_identifier(original_email))

    def test_staff_cannot_self_delete(self):
        """Staff accounts are removed by another staff member, as in the console."""
        staff = UserFactory(is_staff=True)
        self.login_as(staff)

        self.assertEqual(self.client.get("/profile/delete/").status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(self.client.post("/profile/delete/").status_code, HTTPStatus.FORBIDDEN)

        staff.refresh_from_db()
        self.assertTrue(staff.is_active)

    def _make_sole_admin_with_other_member(self):
        target = UserFactory()
        org = Organisation.objects.create(name="Shared Org")
        OrganisationMembership.objects.create(user=target, organisation=org, role=ROLE_ADMIN)
        OrganisationMembership.objects.create(user=UserFactory(), organisation=org, role=ROLE_PROJECT_MANAGER)
        UserFactory(is_staff=True)
        return target

    def test_repeat_deferred_request_notifies_staff_once(self):
        """Resubmitting a pending request (double-click, retry) doesn't re-email staff."""
        target = self._make_sole_admin_with_other_member()
        self.login_as(target)

        with self.captureOnCommitCallbacks(execute=True):
            self.client.post("/profile/delete/")
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post("/profile/delete/")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(ErasureRequest.objects.filter(user=target).count(), 1)

    def test_deferred_request_survives_mail_failure(self):
        """A mail outage is logged, not shown to the user; the request is still recorded."""
        target = self._make_sole_admin_with_other_member()
        self.login_as(target)

        with (
            mock.patch("django.core.mail.send_mail", side_effect=OSError("SMTP down")),
            self.assertLogs("home.services.user", level="ERROR"),
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.client.post("/profile/delete/")

        self.assertRedirects(response, "/profile/")
        self.assertTrue(ErasureRequest.objects.filter(user=target, status=ErasureRequest.Status.PENDING).exists())


class SoleAdminOrganisationHelperTestCase(SORT.test.test_case.ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.service = organisation_service

    def test_sole_admin_with_other_members_is_blocking(self):
        target = UserFactory()
        other_member = UserFactory()
        org = Organisation.objects.create(name="Shared Org")
        OrganisationMembership.objects.create(user=target, organisation=org, role=ROLE_ADMIN)
        OrganisationMembership.objects.create(
            user=other_member, organisation=org, role=ROLE_PROJECT_MANAGER
        )

        blocking = self.service.get_sole_admin_orgs_with_other_members(target)

        self.assertIn(org, blocking)

    def test_no_membership_is_not_blocking(self):
        target = UserFactory()
        self.assertFalse(self.service.get_sole_admin_orgs_with_other_members(target).exists())
