"""
Tests for the invitation acceptance / manager signup flow.

Regression coverage for the 500 error reported in issue #597, where a new user
accepting an invitation hit a server error when the inviter was not an
organisation administrator.
"""

from http import HTTPStatus

import django.urls
from django.contrib.auth import get_user_model
from invitations.models import Invitation

from home.constants import ROLE_PROJECT_MANAGER
from home.models import OrganisationMembership
from home.services import organisation_service
from SORT.test.model_factory import SuperUserFactory, UserFactory
from SORT.test.model_factory.user.constants import PASSWORD
from SORT.test.test_case.view import ViewTestCase

User = get_user_model()

# A password that satisfies Django's default password validators.
SIGNUP_PASSWORD = "Str0ngP@ssw0rd!"


class SignupViewTestCase(ViewTestCase):
    """Test accepting an organisation invitation and registering an account."""

    def setUp(self):
        super().setUp()
        # An administrator who owns an organisation.
        self.admin = UserFactory(email="admin@sort.com")
        self.organisation = organisation_service.create_organisation(
            user=self.admin, name="Test Organisation"
        )
        # A project manager within the same organisation.
        self.project_manager = UserFactory(email="manager@sort.com")
        organisation_service.add_user_to_organisation(
            user=self.admin,
            user_to_add=self.project_manager,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

    def signup(self, invitation: Invitation):
        """POST the registration form for the given invitation."""
        return self.client.post(
            django.urls.reverse("signup", kwargs={"key": invitation.key}),
            data={
                "key": invitation.key,
                "password1": SIGNUP_PASSWORD,
                "password2": SIGNUP_PASSWORD,
            },
        )

    def test_signup_with_admin_invitation_succeeds(self):
        """An invitation sent by an admin lets the new user register."""
        invitation = Invitation.create(email="newbie@sort.com", inviter=self.admin)

        response = self.signup(invitation)

        # The user is redirected to the dashboard after registering.
        self.assertRedirects(
            response,
            django.urls.reverse("dashboard"),
            fetch_redirect_response=False,
        )
        new_user = User.objects.get(email="newbie@sort.com")
        membership = OrganisationMembership.objects.get(
            user=new_user, organisation=self.organisation
        )
        self.assertEqual(membership.role, ROLE_PROJECT_MANAGER)

    def test_signup_with_non_admin_invitation_fails_gracefully(self):
        """
        Regression test for #597: an invitation sent by a project manager must
        not cause a 500 error, and must not leave an orphaned user account.
        """
        invitation = Invitation.create(
            email="newbie@sort.com", inviter=self.project_manager
        )

        response = self.signup(invitation)

        # The form is re-rendered with an error rather than returning a 500.
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # The half-created user account is rolled back.
        self.assertFalse(User.objects.filter(email="newbie@sort.com").exists())

    def test_invite_page_accessible_to_admin(self):
        """An organisation admin can open the invite page."""
        self.client.login(username=self.admin.email, password=PASSWORD)
        response = self.client.get(django.urls.reverse("member_invite"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_invite_page_forbidden_for_project_manager(self):
        """A project manager is redirected away from the invite page."""
        self.client.login(username=self.project_manager.email, password=PASSWORD)
        response = self.client.get(django.urls.reverse("member_invite"))
        self.assertRedirects(
            response,
            django.urls.reverse("members"),
            fetch_redirect_response=False,
        )

    def test_add_user_still_requires_admin_in_service(self):
        """
        The service-layer guard is unchanged: a project manager cannot add
        users directly. The signup fix lives at the view/form layer, not by
        loosening service permissions.
        """
        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            organisation_service.add_user_to_organisation(
                user=self.project_manager,
                user_to_add=UserFactory(email="someone@sort.com"),
                organisation=self.organisation,
                role=ROLE_PROJECT_MANAGER,
            )

    def test_invite_page_accessible_to_superuser(self):
        """
        A superuser who is a member but not an org admin can still open the
        invite page: can_manage_members honours the superuser bypass, matching
        the service-layer permission that backs the action.
        """
        superuser = SuperUserFactory()
        organisation_service.add_user_to_organisation(
            user=self.admin,
            user_to_add=superuser,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )
        self.client.login(username=superuser.email, password=PASSWORD)
        response = self.client.get(django.urls.reverse("member_invite"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_member_delete_forbidden_for_project_manager(self):
        """A project manager is redirected away from the member-remove page."""
        membership = OrganisationMembership.objects.get(
            user=self.project_manager, organisation=self.organisation
        )
        self.client.login(username=self.project_manager.email, password=PASSWORD)
        response = self.client.get(
            django.urls.reverse("member_delete", kwargs={"pk": membership.pk})
        )
        self.assertRedirects(
            response,
            django.urls.reverse("members"),
            fetch_redirect_response=False,
        )
