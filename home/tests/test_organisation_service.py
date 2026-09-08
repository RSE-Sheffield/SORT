"""
Test the organisation service
"""

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

import SORT.test.test_case
from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER, ROLES
from home.models import DataProtectionEvent, Organisation, OrganisationMembership
from home.services import organisation_service
from home.services.organisation import plan_organisation_merge
from SORT.test.model_factory import (
    OrganisationFactory,
    OrganisationMembershipFactory,
    ProjectFactory,
    UserFactory,
)

User = get_user_model()


class OrganisationServiceTestCase(SORT.test.test_case.ServiceTestCase):

    def setUp(self):
        super().setUp()
        self.service = organisation_service
        self.organisation = OrganisationFactory()
        self.manager: User = self.organisation.members.first()
        self.manager.first_name = "Manager"
        self.another_user = UserFactory()
        self.factory = RequestFactory()

    def _make_request(self, user):
        request = self.factory.get("/")
        request.user = user
        request.session = SessionStore()
        return request

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

    def test_create_organisation_when_already_a_member(self):
        """
        A user who already belongs to an organisation can still create
        (and join) another one (issue #675).
        """
        self.assertTrue(self.service.can_create_organisation(self.manager))

        organisation = self.service.create_organisation(
            user=self.manager,
            name="A second organisation",
            description="",
        )

        self.assertEqual(
            {self.organisation.pk, organisation.pk},
            self.service.get_user_organisation_ids(self.manager),
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
        self.service.can_create_organisation(user=user)
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


class ActiveOrganisationTestCase(SORT.test.test_case.ServiceTestCase):
    """Tests for the session-backed "active organisation" concept (#675)."""

    def setUp(self):
        super().setUp()
        self.service = organisation_service
        self.factory = RequestFactory()

    def _make_request(self, user):
        request = self.factory.get("/")
        request.user = user
        request.session = SessionStore()
        return request

    def test_anonymous_user_has_no_active_organisation(self):
        from django.contrib.auth.models import AnonymousUser

        request = self._make_request(AnonymousUser())
        self.assertIsNone(self.service.get_active_organisation(request))

    def test_user_with_no_organisations_has_no_active_organisation(self):
        request = self._make_request(self.user)
        request.session["active_organisation_id"] = 999
        self.assertIsNone(self.service.get_active_organisation(request))
        self.assertNotIn("active_organisation_id", request.session)

    def test_user_with_one_organisation_is_auto_selected(self):
        membership = OrganisationMembershipFactory(
            user=self.user, organisation=OrganisationFactory()
        )
        request = self._make_request(self.user)

        organisation = self.service.get_active_organisation(request)

        self.assertEqual(membership.organisation, organisation)
        self.assertEqual(
            membership.organisation.id, request.session["active_organisation_id"]
        )

    def test_user_with_multiple_organisations_defaults_to_earliest_joined(self):
        first = OrganisationMembershipFactory(
            user=self.user, organisation=OrganisationFactory()
        )
        second = OrganisationMembershipFactory(
            user=self.user, organisation=OrganisationFactory()
        )
        request = self._make_request(self.user)

        organisation = self.service.get_active_organisation(request)

        self.assertEqual(first.organisation, organisation)
        self.assertEqual(
            first.organisation.id, request.session["active_organisation_id"]
        )
        self.assertNotEqual(second.organisation, organisation)

    def test_active_organisation_choice_persists_via_session(self):
        OrganisationMembershipFactory(user=self.user, organisation=OrganisationFactory())
        second = OrganisationMembershipFactory(
            user=self.user, organisation=OrganisationFactory()
        )
        request = self._make_request(self.user)
        request.session["active_organisation_id"] = second.organisation.id

        organisation = self.service.get_active_organisation(request)

        self.assertEqual(second.organisation, organisation)

    def test_stale_active_organisation_falls_back_to_valid_membership(self):
        first = OrganisationMembershipFactory(
            user=self.user, organisation=OrganisationFactory()
        )
        removed = OrganisationMembershipFactory(
            user=self.user, organisation=OrganisationFactory()
        )
        request = self._make_request(self.user)
        request.session["active_organisation_id"] = removed.organisation.id

        # The user has since been removed from that organisation.
        removed.delete()

        organisation = self.service.get_active_organisation(request)

        self.assertEqual(first.organisation, organisation)
        self.assertEqual(
            first.organisation.id, request.session["active_organisation_id"]
        )

    def test_set_active_organisation(self):
        OrganisationMembershipFactory(user=self.user, organisation=OrganisationFactory())
        second = OrganisationMembershipFactory(
            user=self.user, organisation=OrganisationFactory()
        )
        request = self._make_request(self.user)

        self.service.set_active_organisation(request, second.organisation)

        self.assertEqual(
            second.organisation, self.service.get_active_organisation(request)
        )

    def test_get_user_organisations(self):
        first = OrganisationMembershipFactory(
            user=self.user, organisation=OrganisationFactory()
        )
        second = OrganisationMembershipFactory(
            user=self.user, organisation=OrganisationFactory()
        )

        organisations = self.service.get_user_organisations(self.user)

        self.assertEqual(
            {first.organisation.pk, second.organisation.pk},
            set(organisations.values_list("pk", flat=True)),
        )


class OrganisationMergeTestCase(SORT.test.test_case.ServiceTestCase):
    """Tests for the org-merge tool (issue #676)."""

    def setUp(self):
        super().setUp()
        self.service = organisation_service
        self.source = OrganisationFactory()
        self.target = OrganisationFactory()
        self.source_admin = self.source.members.first()
        self.target_admin = self.target.members.first()

    def test_plan_merge_into_self_raises(self):
        with self.assertRaises(ValueError):
            plan_organisation_merge(self.source, self.source)

    def test_plan_moves_projects_and_non_colliding_memberships(self):
        project = ProjectFactory(organisation=self.source)

        plan = plan_organisation_merge(self.source, self.target)

        self.assertEqual([project], plan.projects)
        self.assertEqual(
            [self.source_admin.pk], [m.user.pk for m in plan.memberships_to_move]
        )
        self.assertEqual([], plan.memberships_to_drop)

    def test_plan_drops_duplicate_membership_keeping_target_role(self):
        # source_admin is ADMIN in source; make them a plain member of target too.
        OrganisationMembershipFactory(
            user=self.source_admin,
            organisation=self.target,
            role=ROLE_PROJECT_MANAGER,
        )

        plan = plan_organisation_merge(self.source, self.target)

        self.assertEqual([], plan.memberships_to_move)
        self.assertEqual(
            [self.source_admin.pk], [m.user.pk for m in plan.memberships_to_drop]
        )

    def test_merge_requires_staff(self):
        with self.assertRaises(PermissionDenied):
            self.service.merge_organisations(self.user, self.source, self.target)

    def test_merge_moves_projects_and_memberships_and_deletes_source(self):
        project = ProjectFactory(organisation=self.source)

        self.service.merge_organisations(self.superuser, self.source, self.target)

        project.refresh_from_db()
        self.assertEqual(self.target, project.organisation)
        self.assertTrue(
            OrganisationMembership.objects.filter(
                user=self.source_admin, organisation=self.target
            ).exists()
        )
        self.assertFalse(Organisation.objects.filter(pk=self.source.pk).exists())

    def test_merge_drops_duplicate_membership_keeping_target_role(self):
        OrganisationMembershipFactory(
            user=self.source_admin,
            organisation=self.target,
            role=ROLE_PROJECT_MANAGER,
        )

        self.service.merge_organisations(self.superuser, self.source, self.target)

        membership = OrganisationMembership.objects.get(
            user=self.source_admin, organisation=self.target
        )
        self.assertEqual(ROLE_PROJECT_MANAGER, membership.role)
        self.assertEqual(
            1,
            OrganisationMembership.objects.filter(
                user=self.source_admin, organisation=self.target
            ).count(),
        )

    def test_merge_records_audit_events(self):
        OrganisationMembershipFactory(
            user=self.source_admin,
            organisation=self.target,
            role=ROLE_PROJECT_MANAGER,
        )

        self.service.merge_organisations(self.superuser, self.source, self.target)

        self.assertTrue(
            DataProtectionEvent.objects.filter(
                event_type=DataProtectionEvent.EventType.ORGANISATION_MERGED,
                actioned_by=self.superuser,
            ).exists()
        )
        self.assertTrue(
            DataProtectionEvent.objects.filter(
                event_type=DataProtectionEvent.EventType.MEMBERSHIP_REMOVED,
                actioned_by=self.superuser,
            ).exists()
        )
