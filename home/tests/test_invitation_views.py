"""
Unit tests for invitation views and functionality
"""

from http import HTTPStatus

import django.urls
from django.contrib.auth import get_user_model
from invitations.models import Invitation

from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from home.models import OrganisationMembership
from SORT.test.model_factory import OrganisationFactory, UserFactory
from SORT.test.test_case import ViewTestCase

User = get_user_model()


class InvitationViewTestCase(ViewTestCase):
    """
    Test invitation functionality for inviting users to organisations
    """

    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory()
        self.admin_user = self.user
        # Create additional test users
        self.user1 = UserFactory(email="user1@example.com")
        self.user1.set_password("user1")
        self.user1.save()
        self.user2 = UserFactory(email="user2@example.com")
        self.user2.set_password("user2")
        self.user2.save()
        # Make admin user an admin of the organisation
        OrganisationMembership.objects.create(
            user=self.admin_user,
            organisation=self.organisation,
            role=ROLE_ADMIN,
        )

    def test_invite_new_user_redirects_to_signup(self):
        """
        When a new user (email not in system) accepts an invitation,
        they should be redirected to the signup page.
        """
        self.login()

        # Create an invitation for a new user
        new_user_email = "newuser@example.com"
        invitation = Invitation.create(email=new_user_email, inviter=self.admin_user)
        invitation.sent = django.utils.timezone.now()
        invitation.save()

        # Verify user doesn't exist yet
        self.assertFalse(User.objects.filter(email=new_user_email).exists())

        # Accept the invitation
        response = self.client.post(
            django.urls.reverse("member_invite_accept", kwargs={"key": invitation.key})
        )

        # Should redirect to signup page with the invitation key
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(response.url.startswith("/signup/"))
        self.assertIn(invitation.key, response.url)

    def test_invite_existing_user_redirects_to_login(self):
        """
        When an existing user (email already in system) accepts an invitation,
        they should be redirected to the login page.
        """
        self.login()

        # Create an invitation for an existing user
        existing_user = self.user1
        invitation = Invitation.create(email=existing_user.email, inviter=self.admin_user)
        invitation.sent = django.utils.timezone.now()
        invitation.save()

        # Verify user exists
        self.assertTrue(User.objects.filter(email=existing_user.email).exists())

        # Accept the invitation (logged out)
        self.client.logout()
        response = self.client.post(
            django.urls.reverse("member_invite_accept", kwargs={"key": invitation.key})
        )

        # Should redirect to login page with invitation_key parameter
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn("/login/", response.url)
        self.assertIn(f"invitation_key={invitation.key}", response.url)

    def test_login_with_invitation_adds_user_to_organisation(self):
        """
        When an existing user logs in with an invitation key,
        they should be added to the organisation.
        """
        # Create an invitation for an existing user
        existing_user = self.user1
        invitation = Invitation.create(email=existing_user.email, inviter=self.admin_user)
        invitation.sent = django.utils.timezone.now()
        invitation.save()

        # Verify user is not yet a member of the organisation
        self.assertFalse(
            OrganisationMembership.objects.filter(
                user=existing_user, organisation=self.organisation
            ).exists()
        )

        # Log in with invitation key
        response = self.client.post(
            f"{django.urls.reverse('login')}?invitation_key={invitation.key}",
            data={
                "username": existing_user.email,
                "password": "user1",  # From test fixtures
                "invitation_key": invitation.key,
            },
        )

        # Should redirect to dashboard
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Verify user is now a member of the organisation
        membership = OrganisationMembership.objects.filter(
            user=existing_user, organisation=self.organisation
        ).first()
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, ROLE_PROJECT_MANAGER)

        # Verify invitation is marked as accepted
        invitation.refresh_from_db()
        self.assertTrue(invitation.accepted)

    def test_login_with_invitation_for_wrong_email_shows_error(self):
        """
        When a user logs in with an invitation key for a different email,
        they should see an error message.
        """
        # Create an invitation for user1
        user1 = self.user1
        invitation = Invitation.create(email=user1.email, inviter=self.admin_user)
        invitation.sent = django.utils.timezone.now()
        invitation.save()

        # Try to log in as user2 with user1's invitation
        user2 = self.user2
        response = self.client.post(
            f"{django.urls.reverse('login')}?invitation_key={invitation.key}",
            data={
                "username": user2.email,
                "password": "user2",  # From test fixtures
                "invitation_key": invitation.key,
            },
            follow=True,
        )

        # Should show error message
        messages = list(response.context["messages"])
        self.assertTrue(
            any("different email address" in str(m) for m in messages),
            "Expected error message about different email address",
        )

        # User should not be added to organisation
        self.assertFalse(
            OrganisationMembership.objects.filter(
                user=user2, organisation=self.organisation
            ).exists()
        )

    def test_login_with_expired_invitation_shows_error(self):
        """
        When a user logs in with an expired invitation,
        they should see an error message.
        """
        import datetime
        from django.utils import timezone

        existing_user = self.user1
        invitation = Invitation.create(email=existing_user.email, inviter=self.admin_user)
        # Set invitation as sent 31 days ago (default expiry is 30 days)
        invitation.sent = timezone.now() - datetime.timedelta(days=31)
        invitation.save()

        # Try to log in with expired invitation
        response = self.client.post(
            f"{django.urls.reverse('login')}?invitation_key={invitation.key}",
            data={
                "username": existing_user.email,
                "password": "user1",
                "invitation_key": invitation.key,
            },
            follow=True,
        )

        # Should show error message
        messages = list(response.context["messages"])
        self.assertTrue(
            any("expired" in str(m) for m in messages),
            "Expected error message about expired invitation",
        )

        # User should not be added to organisation
        self.assertFalse(
            OrganisationMembership.objects.filter(
                user=existing_user, organisation=self.organisation
            ).exists()
        )

    def test_login_with_already_accepted_invitation_shows_info(self):
        """
        When a user logs in with an already-accepted invitation,
        they should see an info message.
        """
        existing_user = self.user1
        invitation = Invitation.create(email=existing_user.email, inviter=self.admin_user)
        invitation.sent = django.utils.timezone.now()
        invitation.accepted = True
        invitation.save()

        # Try to log in with already-accepted invitation
        response = self.client.post(
            f"{django.urls.reverse('login')}?invitation_key={invitation.key}",
            data={
                "username": existing_user.email,
                "password": "user1",
                "invitation_key": invitation.key,
            },
            follow=True,
        )

        # Should show info message
        messages = list(response.context["messages"])
        self.assertTrue(
            any("already been accepted" in str(m) for m in messages),
            "Expected info message about already-accepted invitation",
        )

    def test_login_as_existing_member_shows_info(self):
        """
        When a user who is already a member logs in with an invitation,
        they should see an info message.
        """
        existing_user = self.user1

        # Add user to organisation first
        OrganisationMembership.objects.create(
            user=existing_user,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

        invitation = Invitation.create(email=existing_user.email, inviter=self.admin_user)
        invitation.sent = django.utils.timezone.now()
        invitation.save()

        # Try to log in with invitation
        response = self.client.post(
            f"{django.urls.reverse('login')}?invitation_key={invitation.key}",
            data={
                "username": existing_user.email,
                "password": "user1",
                "invitation_key": invitation.key,
            },
            follow=True,
        )

        # Should show info message
        messages = list(response.context["messages"])
        self.assertTrue(
            any("already a member" in str(m) for m in messages),
            "Expected info message about already being a member",
        )
