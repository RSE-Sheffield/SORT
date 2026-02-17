"""
Test the add existing member form and functionality
"""

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

import SORT.test.test_case
from home.constants import ROLE_PROJECT_MANAGER
from home.forms.add_existing_member import AddExistingMemberForm
from home.models import OrganisationMembership
from SORT.test.model_factory import OrganisationFactory, UserFactory
from SORT.test.model_factory.user.constants import PASSWORD

User = get_user_model()


class AddExistingMemberFormTestCase(TestCase):
    """Test the AddExistingMemberForm"""

    def setUp(self):
        self.organisation = OrganisationFactory()
        self.admin_user = self.organisation.members.first()
        self.existing_user = UserFactory()

    def test_form_valid_with_existing_user(self):
        """Test that the form validates when given an existing user's email"""
        form = AddExistingMemberForm(
            data={
                "email": self.existing_user.email,
                "role": ROLE_PROJECT_MANAGER,
            },
            organisation=self.organisation,
            user=self.admin_user,
        )

        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        self.assertEqual(form.get_user(), self.existing_user)
        self.assertFalse(
            hasattr(form, "is_duplicate") and form.is_duplicate,
            "User should not be marked as duplicate",
        )

    def test_form_invalid_with_nonexistent_user(self):
        """Test that the form is invalid when given a non-existent email"""
        form = AddExistingMemberForm(
            data={
                "email": "nonexistent@example.com",
                "role": ROLE_PROJECT_MANAGER,
            },
            organisation=self.organisation,
            user=self.admin_user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("No user with email address", form.errors["email"][0])

    def test_form_idempotent_with_existing_member(self):
        """Test that the form is valid but marks duplicates when user is already a member"""
        # Add user to organisation first
        OrganisationMembership.objects.create(
            user=self.existing_user,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

        form = AddExistingMemberForm(
            data={
                "email": self.existing_user.email,
                "role": ROLE_PROJECT_MANAGER,
            },
            organisation=self.organisation,
            user=self.admin_user,
        )

        self.assertTrue(form.is_valid(), "Form should be valid even for duplicate members")
        self.assertTrue(
            hasattr(form, "is_duplicate") and form.is_duplicate,
            "User should be marked as duplicate",
        )


class AddExistingMemberViewTestCase(SORT.test.test_case.ViewTestCase):
    """Test the MyOrganisationInviteView for adding existing members"""

    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory()
        self.admin_user = self.organisation.members.first()
        self.existing_user = UserFactory()
        self.url = reverse("member_invite")

    def test_add_existing_user_success(self):
        """Test successfully adding an existing user to organisation"""
        self.client.login(username=self.admin_user.email, password=PASSWORD)

        response = self.client.post(
            self.url,
            data={
                "email": self.existing_user.email,
                "role": ROLE_PROJECT_MANAGER,
                "add_existing_submit": "1",
            },
            follow=True,
        )

        # Check that user was added
        self.assertTrue(
            OrganisationMembership.objects.filter(
                user=self.existing_user, organisation=self.organisation
            ).exists(),
            "User should be added to organisation",
        )

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                self.existing_user.email in str(msg) and "has been added" in str(msg)
                for msg in messages
            ),
            "Success message should be displayed",
        )

    def test_add_existing_user_idempotent(self):
        """Test that adding an existing member doesn't fail (idempotent)"""
        # Add user to organisation first
        OrganisationMembership.objects.create(
            user=self.existing_user,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

        self.client.login(username=self.admin_user.email, password=PASSWORD)

        response = self.client.post(
            self.url,
            data={
                "email": self.existing_user.email,
                "role": ROLE_PROJECT_MANAGER,
                "add_existing_submit": "1",
            },
            follow=True,
        )

        # Check that membership still exists (no errors)
        membership_count = OrganisationMembership.objects.filter(
            user=self.existing_user, organisation=self.organisation
        ).count()
        self.assertEqual(membership_count, 1, "Should still have exactly one membership")

        # Check info message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("already a member" in str(msg) for msg in messages),
            "Info message should indicate user is already a member",
        )

    def test_add_nonexistent_user_fails(self):
        """Test that adding a non-existent user shows an error"""
        self.client.login(username=self.admin_user.email, password=PASSWORD)

        response = self.client.post(
            self.url,
            data={
                "email": "nonexistent@example.com",
                "role": ROLE_PROJECT_MANAGER,
                "add_existing_submit": "1",
            },
            follow=False,
        )

        # Check that form is shown with error
        self.assertIn("add_existing_form", response.context)
        form = response.context["add_existing_form"]
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_view_displays_both_forms(self):
        """Test that the view displays both invite and add existing forms"""
        self.client.login(username=self.admin_user.email, password=PASSWORD)

        response = self.client.get(self.url)

        self.assertIn("invite_form", response.context)
        self.assertIn("add_existing_form", response.context)

    def test_non_admin_cannot_add_users(self):
        """Test that non-admin users cannot add members"""
        # Create a project manager (non-admin) user
        project_manager = UserFactory()
        OrganisationMembership.objects.create(
            user=project_manager,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

        self.client.login(username=project_manager.email, password=PASSWORD)

        self.client.post(
            self.url,
            data={
                "email": self.existing_user.email,
                "role": ROLE_PROJECT_MANAGER,
                "add_existing_submit": "1",
            },
            follow=True,
        )

        # Check that user was NOT added (permission denied should prevent it)
        # Note: The service layer should prevent this, but the view should handle it gracefully
        self.assertFalse(
            OrganisationMembership.objects.filter(
                user=self.existing_user, organisation=self.organisation
            ).exists(),
            "Non-admin should not be able to add users",
        )


class AddExistingMemberServiceTestCase(SORT.test.test_case.ServiceTestCase):
    """Test the organisation service add_user_to_organisation method with existing users"""

    def setUp(self):
        super().setUp()
        from home.services import organisation_service

        self.service = organisation_service
        self.organisation = OrganisationFactory()
        self.admin_user = self.organisation.members.first()
        self.existing_user = UserFactory()

    def test_service_add_existing_user(self):
        """Test that the service can add an existing user"""
        membership = self.service.add_user_to_organisation(
            user=self.admin_user,
            user_to_add=self.existing_user,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

        self.assertEqual(membership.user, self.existing_user)
        self.assertEqual(membership.organisation, self.organisation)
        self.assertEqual(membership.role, ROLE_PROJECT_MANAGER)
        self.assertEqual(membership.added_by, self.admin_user)

    def test_service_requires_admin_permission(self):
        """Test that only admins can add users"""
        project_manager = UserFactory()
        OrganisationMembership.objects.create(
            user=project_manager,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

        with self.assertRaises(PermissionDenied):
            self.service.add_user_to_organisation(
                user=project_manager,
                user_to_add=self.existing_user,
                organisation=self.organisation,
                role=ROLE_PROJECT_MANAGER,
            )
