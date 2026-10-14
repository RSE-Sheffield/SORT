from http import HTTPStatus

import SORT.test.test_case
from SORT.test.model_factory import UserFactory
from SORT.test.model_factory.user.constants import PASSWORD

from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from home.models import DataProtectionEvent, ErasureRequest, Organisation, OrganisationMembership


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


class SoleAdminOrganisationHelperTestCase(SORT.test.test_case.ServiceTestCase):
    def setUp(self):
        super().setUp()
        from home.services import organisation_service

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
