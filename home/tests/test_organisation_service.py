"""
Test the organisation service
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

import SORT.test.test_case
from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER, ROLES
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

    def test_get_user_role_returns_correct_role(self):
        """Test get_user_role returns the correct role for a user"""
        role = self.service.get_user_role(self.manager, self.organisation)
        self.assertEqual(role, ROLE_ADMIN)

    def test_get_user_role_returns_none_for_non_member(self):
        """Test get_user_role returns None for non-members"""
        role = self.service.get_user_role(self.another_user, self.organisation)
        self.assertIsNone(role)

    def test_get_user_role_with_anonymous_user(self):
        """Test get_user_role handles anonymous user gracefully"""
        from django.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()
        role = self.service.get_user_role(anon, self.organisation)
        self.assertIsNone(role)

    def test_can_view_project_manager(self):
        """Test that project managers can view organisation"""
        # Add user as project manager
        OrganisationMembership.objects.create(
            user=self.user,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

        self.assertTrue(self.service.can_view(self.user, self.organisation))

    def test_can_view_non_member(self):
        """Test that non-members cannot view organisation"""
        self.assertFalse(self.service.can_view(self.another_user, self.organisation))

    def test_can_edit_admin_only(self):
        """Test that only admins can edit organisation"""
        # Add user as project manager
        OrganisationMembership.objects.create(
            user=self.user,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

        # Project manager should not be able to edit
        self.assertFalse(self.service.can_edit(self.user, self.organisation))

        # Admin should be able to edit
        self.assertTrue(self.service.can_edit(self.manager, self.organisation))

    def test_can_edit_superuser(self):
        """Test that superuser can edit any organisation"""
        self.assertTrue(self.service.can_edit(self.superuser, self.organisation))

    def test_can_delete_admin_only(self):
        """Test that only admins can delete organisation"""
        # Add user as project manager
        OrganisationMembership.objects.create(
            user=self.user,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

        # Project manager should not be able to delete
        self.assertFalse(self.service.can_delete(self.user, self.organisation))

        # Admin should be able to delete
        self.assertTrue(self.service.can_delete(self.manager, self.organisation))

    def test_can_delete_superuser(self):
        """Test that superuser can delete any organisation"""
        self.assertTrue(self.service.can_delete(self.superuser, self.organisation))

    def test_can_manage_members_admin_only(self):
        """Test that only admins can manage members"""
        # Add user as project manager
        OrganisationMembership.objects.create(
            user=self.user,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

        # Project manager should not be able to manage members
        self.assertFalse(
            self.service.can_manage_members(self.user, self.organisation)
        )

        # Admin should be able to manage members
        self.assertTrue(
            self.service.can_manage_members(self.manager, self.organisation)
        )

    def test_can_manage_members_non_member(self):
        """Test that non-members cannot manage members"""
        self.assertFalse(
            self.service.can_manage_members(self.another_user, self.organisation)
        )

    def test_can_create_new_user(self):
        """Test that user without organisation can create one"""
        # User without org should be able to create
        self.assertTrue(self.service.can_create(self.user))

    def test_can_create_existing_member(self):
        """Test that user with organisation cannot create another"""
        # Manager already has an organisation
        self.assertFalse(self.service.can_create(self.manager))

    def test_can_create_superuser(self):
        """Test that superuser can always create organisation"""
        self.assertTrue(self.service.can_create(self.superuser))

    def test_get_organisation_with_permission(self):
        """Test get_organisation returns org when user has permission"""
        org = self.service.get_organisation(self.manager, self.organisation)
        self.assertEqual(org, self.organisation)

    def test_get_organisation_without_permission(self):
        """Test get_organisation raises error when user lacks permission"""
        with self.assertRaises(PermissionDenied):
            self.service.get_organisation(self.another_user, self.organisation)

    def test_get_user_organisation_returns_first(self):
        """Test get_user_organisation returns user's first organisation"""
        org = self.service.get_user_organisation(self.manager)
        self.assertEqual(org, self.organisation)

    def test_get_user_organisation_unauthenticated(self):
        """Test get_user_organisation returns None for unauthenticated user"""
        from django.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()
        org = self.service.get_user_organisation(anon)
        self.assertIsNone(org)

    def test_get_user_organisation_no_org(self):
        """Test get_user_organisation returns None when user has no organisation"""
        org = self.service.get_user_organisation(self.another_user)
        self.assertIsNone(org)

    def test_get_user_organisation_ids(self):
        """Test get_user_organisation_ids returns set of IDs"""
        org_ids = self.service.get_user_organisation_ids(self.manager)
        self.assertIsInstance(org_ids, set)
        self.assertIn(self.organisation.pk, org_ids)

    def test_get_user_organisation_ids_multiple_orgs(self):
        """Test get_user_organisation_ids with multiple organisations"""
        org2 = OrganisationFactory()
        OrganisationMembership.objects.create(
            user=self.manager, organisation=org2, role=ROLE_ADMIN
        )

        org_ids = self.service.get_user_organisation_ids(self.manager)
        self.assertEqual(len(org_ids), 2)
        self.assertIn(self.organisation.pk, org_ids)
        self.assertIn(org2.pk, org_ids)

    def test_get_user_organisation_ids_no_orgs(self):
        """Test get_user_organisation_ids returns empty set for user with no orgs"""
        org_ids = self.service.get_user_organisation_ids(self.another_user)
        self.assertIsInstance(org_ids, set)
        self.assertEqual(len(org_ids), 0)

    def test_add_user_to_organisation_invalid_role(self):
        """Test that invalid role raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.service.add_user_to_organisation(
                user=self.manager,
                user_to_add=self.user,
                organisation=self.organisation,
                role="invalid_role",
            )

        self.assertIn("Role must be either", str(context.exception))

    def test_add_user_to_organisation_as_project_manager(self):
        """Test adding user with project manager role"""
        membership = self.service.add_user_to_organisation(
            user=self.manager,
            user_to_add=self.user,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
        )

        self.assertEqual(membership.role, ROLE_PROJECT_MANAGER)
        self.assertEqual(membership.added_by, self.manager)

    def test_update_organisation_updates_fields(self):
        """Test that update_organisation modifies fields correctly"""
        new_name = "Updated Name"
        new_description = "Updated Description"

        self.service.update_organisation(
            self.manager,
            self.organisation,
            {"name": new_name, "description": new_description},
        )

        self.organisation.refresh_from_db()
        self.assertEqual(self.organisation.name, new_name)
        self.assertEqual(self.organisation.description, new_description)

    def test_update_organisation_partial_update(self):
        """Test that update_organisation handles partial updates"""
        original_name = self.organisation.name
        new_description = "Only description changed"

        self.service.update_organisation(
            self.manager, self.organisation, {"description": new_description}
        )

        self.organisation.refresh_from_db()
        self.assertEqual(self.organisation.name, original_name)
        self.assertEqual(self.organisation.description, new_description)

    def test_get_organisation_projects_with_metrics(self):
        """Test get_organisation_projects returns projects with metrics"""
        from SORT.test.model_factory import ProjectFactory

        ProjectFactory(organisation=self.organisation)
        ProjectFactory(organisation=self.organisation)

        projects = self.service.get_organisation_projects(
            self.organisation, self.manager, with_metrics=True
        )

        self.assertEqual(projects.count(), 2)

    def test_get_organisation_projects_without_metrics(self):
        """Test get_organisation_projects returns projects without metrics"""
        from SORT.test.model_factory import ProjectFactory

        ProjectFactory(organisation=self.organisation)

        projects = self.service.get_organisation_projects(
            self.organisation, self.manager, with_metrics=False
        )

        self.assertEqual(projects.count(), 1)

    def test_get_organisation_projects_unauthorized(self):
        """Test get_organisation_projects returns empty for unauthorized user"""
        from SORT.test.model_factory import ProjectFactory

        ProjectFactory(organisation=self.organisation)

        projects = self.service.get_organisation_projects(
            self.organisation, self.another_user, with_metrics=True
        )

        self.assertEqual(projects.count(), 0)

    def test_create_organisation_adds_creator_as_admin(self):
        """Test that creator is added as admin when creating organisation"""
        new_org = self.service.create_organisation(
            user=self.user,
            name="New Organisation",
            description="Test description",
        )

        membership = OrganisationMembership.objects.get(
            user=self.user, organisation=new_org
        )

        self.assertEqual(membership.role, ROLE_ADMIN)
        self.assertEqual(membership.added_by, self.user)

    def test_create_organisation_with_empty_description(self):
        """Test creating organisation without description"""
        new_org = self.service.create_organisation(
            user=self.user,
            name="Org Without Description",
        )

        self.assertEqual(new_org.description, "")
