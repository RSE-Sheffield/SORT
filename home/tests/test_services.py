import django.test
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from home.services import organisation_service
from home.services import project_service
from survey.services import survey_service
from .model_factory import UserFactory, OrganisationFactory, ProjectFactory, SurveyFactory
from ..models import Organisation, OrganisationMembership
from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER


class OrganisationServiceTest(django.test.TestCase):
    """
    Testing organisation creation
    """

    def setUp(self):
        self.manager1 = UserFactory()
        self.manager2 = UserFactory()
        self.manager3 = UserFactory()
        self.org = OrganisationFactory()
        OrganisationMembership.objects.create(user=self.manager1, organisation=self.org, role=ROLE_ADMIN)
        self.project = ProjectFactory(organisation=self.org)
        self.survey = SurveyFactory(project=self.project)

    def test_create_organisation(self):
        org_name = "Test org creation"
        manager = UserFactory()
        created_org = organisation_service.create_organisation(manager, org_name)

        # Check org object is returned
        self.assertTrue(isinstance(created_org, Organisation))
        # Check the org exists
        self.assertEqual(Organisation.objects.filter(name=org_name).count(), 1)

    def test_update_organisation(self):
        new_values = {
            "name": "New name",
            "description": "New description",
        }

        organisation_service.update_organisation(self.manager1, self.org, new_values)
        self.assertEqual(new_values["name"], self.org.name)
        self.assertEqual(new_values["description"], self.org.description)

        with self.assertRaises(PermissionDenied):
            organisation_service.update_organisation(self.manager2, self.org, new_values)

    def test_add_user_to_organisation(self):
        organisation_service.add_user_to_organisation(user=self.manager1,
                                                      user_to_add=self.manager2,
                                                      organisation=self.org,
                                                      role=ROLE_ADMIN)

        membership = OrganisationMembership.objects.filter(user=self.manager2, organisation=self.org).first()
        self.assertEqual(membership.user, self.manager2)
        self.assertEqual(membership.organisation, self.org)
        self.assertEqual(membership.role, ROLE_ADMIN)

    def test_add_user_to_organisation_no_permission(self):
        with self.assertRaises(PermissionDenied):
            organisation_service.add_user_to_organisation(user=self.manager2,
                                                          user_to_add=self.manager3,
                                                          organisation=self.org,
                                                          role=ROLE_ADMIN)

    def test_remove_user_from_organisation(self):
        # Add manager3 and check that they're a member
        OrganisationMembership.objects.create(user=self.manager3, organisation=self.org, role=ROLE_PROJECT_MANAGER)
        self.assertEqual(OrganisationMembership.objects.filter(user=self.manager3, organisation=self.org).count(), 1)
        # Remove manager 3 then check
        organisation_service.remove_user_from_organisation(self.manager1, self.org, self.manager3)
        self.assertEqual(OrganisationMembership.objects.filter(user=self.manager3, organisation=self.org).count(), 0)

        # Remove manager not currently in org, should not throw an error
        organisation_service.remove_user_from_organisation(self.manager1, self.org, self.manager3)

        with self.assertRaises(PermissionDenied):
            organisation_service.remove_user_from_organisation(self.manager2, self.org, self.manager1)

    def test_get_organisation_members(self):
        self.assertEqual(organisation_service.get_organisation_members(self.manager1, self.org).count(), 1)

        organisation_service.add_user_to_organisation(user=self.manager1,
                                                      user_to_add=self.manager2,
                                                      organisation=self.org,
                                                      role=ROLE_ADMIN)

        self.assertEqual(organisation_service.get_organisation_members(self.manager1, self.org).count(), 2)

        with self.assertRaises(PermissionDenied):
            organisation_service.get_organisation_members(self.manager3, self.org)


class ServicesPermissionsTest(django.test.TestCase):
    """
    Testing all base permissions (view, edit, create & delete) for all services
    """

    def setUp(self):
        self.manager1 = UserFactory()
        self.manager2 = UserFactory()
        self.org = OrganisationFactory()
        OrganisationMembership.objects.create(user=self.manager1, organisation=self.org, role=ROLE_ADMIN)
        self.project = ProjectFactory(organisation=self.org)
        self.survey = SurveyFactory(project=self.project)

    def test_organisation_view_permission(self):
        self.assertTrue(organisation_service.can_view(self.manager1, self.org), "Manager cannot view own org")
        self.assertFalse(organisation_service.can_view(self.manager2, self.org), "Manager can view other org")

    def test_organisation_create_permission(self):
        self.assertFalse(organisation_service.can_create(self.manager1),
                         "Manager can create another org when they're a member of an existing one")
        self.assertTrue(organisation_service.can_create(self.manager2), "Manager cannot create org")

    def test_organisation_edit_permission(self):
        self.assertTrue(organisation_service.can_edit(self.manager1, self.org), "Manager cannot edit own org")
        self.assertFalse(organisation_service.can_edit(self.manager2, self.org), "Manager can edit other org")

    def test_organisation_delete_permission(self):
        self.assertTrue(organisation_service.can_delete(self.manager1, self.org), "Manager cannot delete own org")
        self.assertFalse(organisation_service.can_delete(self.manager2, self.org), "Manager can delete other org")

    def test_project_view_permission(self):
        self.assertTrue(project_service.can_view(self.manager1, self.project), "Manager cannot view own project")
        self.assertFalse(project_service.can_view(self.manager2, self.project), "Manager can view other project")

    def test_project_create_permission(self):
        self.assertTrue(project_service.can_create(self.manager1, self.org),
                        "Manager cannot create project in org they belong to")
        self.assertFalse(project_service.can_create(self.manager2, self.org), "Manager can create project in other org")

    def test_project_edit_permission(self):
        self.assertTrue(project_service.can_edit(self.manager1, self.project), "Manager cannot edit own project")
        self.assertFalse(project_service.can_edit(self.manager2, self.project), "Manager can edit other project")

    def test_project_delete_permission(self):
        self.assertTrue(project_service.can_delete(self.manager1, self.project), "Manager cannot delete own project")
        self.assertFalse(project_service.can_delete(self.manager2, self.project), "Manager can delete other project")

    def test_survey_view_permission(self):
        self.assertTrue(survey_service.can_view(self.manager1, self.survey), "Manager cannot view own survey")
        self.assertFalse(survey_service.can_view(self.manager2, self.survey), "Manager can view other survey")

    def test_survey_create_permission(self):
        self.assertTrue(survey_service.can_create(self.manager1, self.project),
                        "Manager cannot create survey in org they belong to")
        self.assertFalse(survey_service.can_create(self.manager2, self.project),
                         "Manager can create survey in other org")

    def test_survey_edit_permission(self):
        self.assertTrue(survey_service.can_edit(self.manager1, self.survey), "Manager cannot edit own survey")
        self.assertFalse(survey_service.can_edit(self.manager2, self.survey), "Manager can edit other survey")

    def test_survey_delete_permission(self):
        self.assertTrue(survey_service.can_delete(self.manager1, self.survey), "Manager cannot delete own survey")
        self.assertFalse(survey_service.can_delete(self.manager2, self.survey), "Manager can delete other survey")
