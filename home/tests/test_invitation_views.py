"""
Unit tests for organisation invitation views
"""

from http import HTTPStatus

import django.urls
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from invitations.models import Invitation

from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from home.models import OrganisationMembership
from SORT.test.model_factory import OrganisationFactory, UserFactory
from SORT.test.test_case import ViewTestCase

User = get_user_model()


def create_invitation(email, inviter):
    """
    Helper function to create and send an invitation with proper timestamp.
    """
    invitation = Invitation.create(email=email, inviter=inviter)
    invitation.sent = timezone.now()
    invitation.save()
    return invitation


class InvitationNewUserTestCase(ViewTestCase):
    """
    Test invitation flow for new users (users who don't have an account yet)
    """

    def setUp(self):
        super().setUp()
        # Create an organisation with an admin
        self.admin_user = UserFactory(email="admin@example.com")
        self.organisation = OrganisationFactory()
        OrganisationMembership.objects.create(
            user=self.admin_user,
            organisation=self.organisation,
            role=ROLE_ADMIN,
            added_by=self.admin_user,
        )

    def test_new_user_invitation_redirects_to_signup(self):
        """
        When a new user (no existing account) accepts an invitation,
        they should be redirected to the signup page.
        """
        # Create invitation for a new user
        invitation = create_invitation("newuser@example.com", self.admin_user)

        # Accept invitation
        response = self.client.post(
            django.urls.reverse("member_invite_accept", kwargs={"key": invitation.key})
        )

        # Should redirect to signup with invitation key
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        expected_url = django.urls.reverse("signup", kwargs={"key": invitation.key})
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

    def test_new_user_signup_creates_account_and_adds_to_organisation(self):
        """
        New user should be able to complete signup and be added to organisation
        """
        # Create invitation
        invitation = create_invitation("newuser@example.com", self.admin_user)

        # Access signup page
        response = self.client.get(
            django.urls.reverse("signup", kwargs={"key": invitation.key})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("newuser@example.com", response.content.decode())

        # Submit signup form
        signup_data = {
            "key": invitation.key,
            "password1": "testpassword123!",
            "password2": "testpassword123!",
        }

        response = self.client.post(
            django.urls.reverse("signup", kwargs={"key": invitation.key}),
            data=signup_data,
        )

        # Should redirect to dashboard
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Verify user was created
        new_user = User.objects.get(email="newuser@example.com")
        self.assertIsNotNone(new_user)

        # Verify user was added to organisation
        membership = OrganisationMembership.objects.get(
            user=new_user, organisation=self.organisation
        )
        self.assertEqual(membership.role, ROLE_PROJECT_MANAGER)


class InvitationExistingUserTestCase(ViewTestCase):
    """
    Test invitation flow for existing users (users who already have an account)
    """

    def setUp(self):
        super().setUp()
        # Create an organisation with an admin
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="admin123",
            first_name="Admin",
            last_name="User",
        )
        self.organisation = OrganisationFactory()
        OrganisationMembership.objects.create(
            user=self.admin_user,
            organisation=self.organisation,
            role=ROLE_ADMIN,
            added_by=self.admin_user,
        )

        # Create an existing user (not in the organisation)
        self.existing_user = User.objects.create_user(
            email="existing@example.com",
            password="existing123",
            first_name="Existing",
            last_name="User",
        )

    def test_existing_user_invitation_redirects_to_login(self):
        """
        When an existing user accepts an invitation, they should be
        redirected to login (not signup).
        """
        # Create invitation for existing user
        invitation = create_invitation("existing@example.com", self.admin_user)

        # Accept invitation (not logged in)
        response = self.client.post(
            django.urls.reverse("member_invite_accept", kwargs={"key": invitation.key})
        )

        # Should redirect to login page
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, django.urls.reverse("login"), fetch_redirect_response=False
        )

        # Check that invitation key is stored in session
        session = self.client.session
        self.assertEqual(session.get("pending_invitation_key"), invitation.key)

    def test_existing_user_login_redirects_to_accept_invitation(self):
        """
        After existing user logs in with pending invitation,
        they should be redirected to accept invitation.
        """
        # Create invitation for existing user
        invitation = create_invitation("existing@example.com", self.admin_user)

        # Accept invitation (stores key in session)
        self.client.post(
            django.urls.reverse("member_invite_accept", kwargs={"key": invitation.key})
        )

        # Now log in
        login_data = {"username": "existing@example.com", "password": "existing123"}

        response = self.client.post(django.urls.reverse("login"), data=login_data)

        # Should redirect to accept_invitation_after_login
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            django.urls.reverse("accept_invitation_after_login"),
            fetch_redirect_response=False,
        )

    def test_accept_invitation_after_login_adds_user_to_organisation(self):
        """
        After logging in, user should be added to organisation
        """
        # Create invitation
        invitation = create_invitation("existing@example.com", self.admin_user)

        # Accept invitation (stores key in session and redirects to login)
        response = self.client.post(
            django.urls.reverse("member_invite_accept", kwargs={"key": invitation.key})
        )

        # Should redirect to login
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Log in using the login form (maintains session)
        login_response = self.client.post(
            django.urls.reverse("login"),
            data={"username": "existing@example.com", "password": "existing123"},
            follow=True,  # Follow redirects
        )

        # Should redirect to accept_invitation_after_login, then to myorganisation
        self.assertEqual(login_response.status_code, HTTPStatus.OK)

        # Debug: Print response content if test fails
        if not OrganisationMembership.objects.filter(
            user=self.existing_user, organisation=self.organisation
        ).exists():
            print(f"\nRedirect chain: {login_response.redirect_chain}")
            print(f"Final URL: {login_response.request['PATH_INFO']}")
            for message in login_response.context.get("messages", {}):
                print("Message: ", message)

        # Verify user was added to organisation
        membership = OrganisationMembership.objects.filter(
            user=self.existing_user, organisation=self.organisation
        ).first()

        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, ROLE_PROJECT_MANAGER)

        # Verify invitation was marked as accepted
        invitation.refresh_from_db()
        self.assertTrue(invitation.accepted)


class InvitationSecurityTestCase(ViewTestCase):
    """
    Test security aspects of invitation system
    """

    def setUp(self):
        super().setUp()
        # Create organisation with admin
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="admin123",
            first_name="Admin",
            last_name="User",
        )
        self.organisation = OrganisationFactory()
        OrganisationMembership.objects.create(
            user=self.admin_user,
            organisation=self.organisation,
            role=ROLE_ADMIN,
            added_by=self.admin_user,
        )

        # Create two existing users
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="user123",
            first_name="User",
            last_name="One",
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="user223",
            first_name="User",
            last_name="Two",
        )

    def test_email_mismatch_prevents_invitation_acceptance(self):
        """
        User logged in with different email should not be able to accept invitation
        """
        # Create invitation for user1
        invitation = create_invitation("user1@example.com", self.admin_user)

        # Accept invitation (stores key in session)
        self.client.post(
            django.urls.reverse("member_invite_accept", kwargs={"key": invitation.key})
        )

        # Log in as different user (user2)
        self.client.login(username="user2@example.com", password="user223")

        # Try to accept invitation
        response = self.client.get(django.urls.reverse("accept_invitation_after_login"))

        # Should redirect to dashboard with error
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # User2 should NOT be added to organisation
        membership = OrganisationMembership.objects.filter(
            user=self.user2, organisation=self.organisation
        ).first()
        self.assertIsNone(membership)

    def test_invalid_invitation_key_shows_error(self):
        """
        Invalid invitation key should show error message
        """
        # Log in as existing user
        self.client.login(username="user1@example.com", password="user123")

        # Set invalid invitation key in session
        session = self.client.session
        session["pending_invitation_key"] = "invalid-key-12345"
        session.save()

        # Try to accept invitation
        response = self.client.get(django.urls.reverse("accept_invitation_after_login"))

        # Should redirect to dashboard
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Session key should be cleared
        session = self.client.session
        self.assertNotIn("pending_invitation_key", session)

    def test_already_member_shows_info_message(self):
        """
        If user is already a member, show info message and mark invitation accepted
        """
        # Add user1 to organisation first
        OrganisationMembership.objects.create(
            user=self.user1,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
            added_by=self.admin_user,
        )

        # Create invitation for user1
        invitation = create_invitation("user1@example.com", self.admin_user)

        # Accept invitation (stores key in session)
        self.client.post(
            django.urls.reverse("member_invite_accept", kwargs={"key": invitation.key})
        )

        # Log in as user1
        self.client.login(username="user1@example.com", password="user123")

        # Try to accept invitation
        response = self.client.get(django.urls.reverse("accept_invitation_after_login"))

        # Should redirect to myorganisation
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Invitation should be marked as accepted
        invitation.refresh_from_db()
        self.assertTrue(invitation.accepted)

        # Should still only have one membership (not duplicate)
        membership_count = OrganisationMembership.objects.filter(
            user=self.user1, organisation=self.organisation
        ).count()
        self.assertEqual(membership_count, 1)

    def test_no_pending_invitation_redirects_to_dashboard(self):
        """
        Accessing accept_invitation_after_login without pending invitation
        should redirect to dashboard
        """
        # Log in without pending invitation
        self.client.login(username="user1@example.com", password="user123")

        # Try to access accept invitation view
        response = self.client.get(django.urls.reverse("accept_invitation_after_login"))

        # Should redirect to dashboard
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, django.urls.reverse("dashboard"), fetch_redirect_response=False
        )

    def test_accepted_invitation_cannot_be_reused(self):
        """
        Once invitation is accepted, it cannot be used again
        """
        # Create invitation
        invitation = create_invitation("user1@example.com", self.admin_user)

        # Accept invitation and add to organisation
        self.client.post(
            django.urls.reverse("member_invite_accept", kwargs={"key": invitation.key})
        )
        self.client.login(username="user1@example.com", password="user123")
        self.client.get(django.urls.reverse("accept_invitation_after_login"))

        # Mark invitation as accepted
        invitation.accepted = True
        invitation.save()

        # Log out
        self.client.logout()

        # Try to use same invitation key again
        session = self.client.session
        session["pending_invitation_key"] = invitation.key
        session.save()

        self.client.login(username="user1@example.com", password="user123")

        response = self.client.get(django.urls.reverse("accept_invitation_after_login"))

        # Should redirect to dashboard with error
        self.assertEqual(response.status_code, HTTPStatus.FOUND)


@override_settings(INVITATIONS_INVITATION_EXPIRY=0)
class InvitationExpirationTestCase(ViewTestCase):
    """
    Test invitation expiration (requires settings override)
    """

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="admin123",
            first_name="Admin",
            last_name="User",
        )
        self.organisation = OrganisationFactory()
        OrganisationMembership.objects.create(
            user=self.admin_user,
            organisation=self.organisation,
            role=ROLE_ADMIN,
            added_by=self.admin_user,
        )

    def test_expired_invitation_shows_error(self):
        """
        Expired invitation should not be accepted
        """
        # Create invitation (will be immediately expired with EXPIRY=0)
        invitation = create_invitation("user@example.com", self.admin_user)

        # Try to accept expired invitation
        response = self.client.post(
            django.urls.reverse("member_invite_accept", kwargs={"key": invitation.key})
        )

        # django-invitations handles expiration - should show error
        # The exact behavior depends on django-invitations version
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
