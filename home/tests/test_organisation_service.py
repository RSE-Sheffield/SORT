"""
Test the organisation service
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from home.services import OrganisationService
from home.models import Organisation
from home.constants import ROLES
from .model_factory import UserFactory

User = get_user_model()


class OrganisationServiceTestCase(TestCase):

    def setUp(self):
        self.service = OrganisationService()
        # Create fake users for testing purposes
        self.user = UserFactory()
        self.superuser = User.objects.create_superuser(first_name="Janet", last_name="Smith",
                                                       email="janet.smith@sort-online.org")

    def test_create_organisation_permission_denied(self):
        """
        Test that a normal user can't create organisations
        """

        # This should raise a permission denied error
        self.assertRaises(
            PermissionDenied,
            self.service.create_organisation,
            user=self.user,
            name="Testing Organisation",
            description="Testing Organisation",
        )

    def test_create_organisation(self):
        user = self.superuser
        name = "Testing Organisation"

        self.service.create_organisation(
            user=user,
            name="Testing Organisation",
            description="Testing Organisation",
        )

        # Ensure it worked and we created a new org.
        self.assertTrue(Organisation.objects.exists(), "No organisation was created")
        self.assertEqual(Organisation.objects.count(), 1, "Unexpected number of organisations")

        organisation = Organisation.objects.first()

        self.assertEqual(organisation.name, name, "Unexpected organisation name")

        # Test the service methods
        role = self.service.get_user_role(user=user, organisation=organisation)
        self.assertIn(role, {role for role, name in ROLES}, "Unexpected role")
        self.service.can_view(user=user, organisation=organisation)
        self.service.can_edit(user=user, organisation=organisation)
        self.service.can_delete(user=user, organisation=organisation)
        self.service.can_manage_members(user=user, organisation=organisation)
        self.service.can_create(user=user)
        self.service.get_user_organisation(user=user)

        # Check member exists in that organisation
        self.assertEqual({organisation.pk}, self.service.get_user_organisation_ids(user=user))
        org_membership = OrganisationMembership.objects.filter(user=user, organisation=organisation).first()
        self.assertEqual(org_membership.user.pk, user.pk)
        self.assertEqual(org_membership.organisation.pk, organisation.pk)
