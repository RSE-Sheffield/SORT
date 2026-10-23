"""
Test project views
"""

from http import HTTPStatus

import django.urls

import SORT.test.test_case
from home.constants import ROLE_PROJECT_MANAGER
from home.models import Project
from SORT.test.model_factory import OrganisationMembershipFactory, ProjectFactory, SurveyFactory


class ProjectViewTestCase(SORT.test.test_case.ViewTestCase):

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()
        self.user = self.project.organisation.members.first()

    def test_project_detail_view(self):
        self.get("project", project_id=self.project.pk)

    def test_project_detail_view_search(self):
        SurveyFactory(project=self.project, name="Alpha survey")
        SurveyFactory(project=self.project, name="Beta survey")
        self.login()
        response = self.client.get(
            django.urls.reverse("project", kwargs=dict(project_id=self.project.pk)),
            {"q": "alpha"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual([survey.name for survey in response.context["surveys"]], ["Alpha survey"])

    def test_project_edit_view(self):
        self.post(
            "project_edit",
            expected_status_code=HTTPStatus.FOUND,
            project_id=self.project.pk,
            data=dict(name="Renamed project", description="New description"),
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Renamed project")
        self.assertEqual(self.project.description, "New description")

    def test_project_create_view(self):
        self.skipTest("Not implemented")

    def test_project_delete_view(self):
        self.post("project_delete", expected_status_code=HTTPStatus.FOUND, pk=self.project.pk)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_project_delete_view_project_manager_denied(self):
        membership = OrganisationMembershipFactory(organisation=self.project.organisation, role=ROLE_PROJECT_MANAGER)
        self.user = membership.user
        self.post("project_delete", expected_status_code=HTTPStatus.FOUND, pk=self.project.pk)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())
