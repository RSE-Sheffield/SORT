"""
Test the organisation service
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

import SORT.test.test_case
from home.constants import ROLE_ADMIN, ROLES
from home.models import Organisation, OrganisationMembership
from home.services import OrganisationService
from SORT.test.model_factory import OrganisationFactory, UserFactory

User = get_user_model()


class OrganisationServiceTestCase(SORT.test.test_case.ServiceTestCase):

    def setUp(self):
        super().setUp()
        self.service = OrganisationService()
        self.organisation = OrganisationFactory()
        self.manager: User = self.organisation.members.first()
        self.manager.first_name = "Manager"
        self.another_user = UserFactory()

    def test_create_organisation(self):
        """
        Test that a normal user can create an organisation
        """
        name = "My test organisation"

        # This should raise a permission denied error
        organisation = self.service.create_organisation(
            user=self.user,
            name=name,
            description="Testing Organisation",
        )

        self.assertEqual(self.user, organisation.members.first(), "Incorrect user")
        self.assertTrue(
            Organisation.objects.filter(name=name).exists(),
            "Organisation doesn't exist",
        )

    def test_create_organisation_as_superuser(self):
        """
        Check that a superuser can create an organisation.
        """

        user = self.superuser
        name = "Testing Organisation"

        organisation = self.service.create_organisation(
            user=user,
            name=name,
            description=name,
        )

        self.assertTrue(isinstance(organisation, Organisation))

        # Ensure it worked and we created a new org.
        self.assertTrue(
            Organisation.objects.filter(name=name).exists(),
            "No organisation with that name was created",
        )
        self.assertEqual(
            Organisation.objects.filter(name=name).count(),
            1,
            "Unexpected number of organisations",
        )

        organisation = Organisation.objects.filter(name=name).first()

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
        self.assertEqual(
            {organisation.pk}, self.service.get_user_organisation_ids(user=user)
        )
        org_membership = OrganisationMembership.objects.filter(
            user=user, organisation=organisation
        ).first()
        self.assertEqual(org_membership.user.pk, user.pk)
        self.assertEqual(org_membership.organisation.pk, organisation.pk)

    def test_update_organisation(self):
        """
        Check that a superuser can modify an existing organisation
        """

        # Modify the organisation
        new_values = dict(
            name="New name",
            description="New description",
        )
        self.service.update_organisation(self.manager, self.organisation, new_values)

        # Check the changes were applied
        self.assertEqual(new_values["name"], self.organisation.name)
        self.assertEqual(new_values["description"], self.organisation.description)

        # Ordinary users can't alter organisations
        with self.assertRaises(PermissionDenied):
            self.service.update_organisation(self.user, self.organisation, new_values)

    def test_add_user_to_organisation(self):
        """
        Check that an organisation administrator can add another user to that organisation.
        """
        organisation = OrganisationFactory()
        # The first manager is an administrator
        OrganisationMembership.objects.create(
            user=self.manager, organisation=organisation, role=ROLE_ADMIN
        )

        # Add the second user
        self.service.add_user_to_organisation(
            user=self.manager,
            user_to_add=self.user,
            organisation=organisation,
            role=ROLE_ADMIN,
        )

        # Check organisation membership
        membership = OrganisationMembership.objects.filter(
            user=self.user, organisation=organisation
        ).first()
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.organisation, organisation)
        self.assertEqual(membership.role, ROLE_ADMIN)

    def test_add_user_to_organisation_no_permission(self):
        organisation = OrganisationFactory()
        with self.assertRaises(PermissionDenied):
            self.service.add_user_to_organisation(
                user=self.manager,
                user_to_add=self.user,
                organisation=organisation,
                role=ROLE_ADMIN,
            )

    def test_remove_user_from_organisation(self):
        self.assertEqual(
            OrganisationMembership.objects.filter(
                user=self.manager, organisation=self.organisation
            ).count(),
            1,
        )

        # Remove manager then check
        self.service.remove_user_from_organisation(
            self.manager, self.organisation, self.manager
        )
        self.assertEqual(
            OrganisationMembership.objects.filter(
                user=self.manager, organisation=self.organisation
            ).count(),
            0,
        )

        with self.assertRaises(PermissionDenied):
            self.service.remove_user_from_organisation(
                self.manager, self.organisation, removed_user=self.user
            )

        # Attempt "hostile takeover" by non-authorised user
        with self.assertRaises(PermissionDenied):
            self.service.remove_user_from_organisation(
                self.user, self.organisation, removed_user=self.manager
            )

    def test_get_organisation_members(self):
        members = self.service.get_organisation_members(self.manager, self.organisation)
        self.assertEqual(
            members.count(), 1, "Unexpected number of organisation members"
        )

        self.service.add_user_to_organisation(
            user=self.manager,
            user_to_add=self.user,
            organisation=self.organisation,
            role=ROLE_ADMIN,
        )

        self.assertEqual(
            self.service.get_organisation_members(
                self.manager, self.organisation
            ).count(),
            2,
            "Unexpected number of organisation members",
        )

        # See if a random user can view the membership
        with self.assertRaises(PermissionDenied):
            self.service.get_organisation_members(self.another_user, self.organisation)
