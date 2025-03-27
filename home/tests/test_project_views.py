"""
Test project views
"""

from http import HTTPStatus

import django.test
import django.urls
from django.contrib.auth import get_user_model

import SORT.test.test_case
from home.services import OrganisationService, ProjectService

User = get_user_model()


class ProjectViewTestCase(SORT.test.test_case.ViewTestCase):

    def setUp(self):
        super().setUp()
        self.project_service = ProjectService()
        self.organisation_service = OrganisationService()

        self.organisation = self.organisation_service.create_organisation(
            user=self.superuser,
            name="My organisation",
            description="This is an org.",
        )
        self.project = self.project_service.create_project(
            user=self.superuser, name="My test project", organisation=self.organisation
        )

    def test_projects_detail_view(self):
        self.login_superuser()
        response = self.client.get(
            django.urls.reverse("project", kwargs=dict(project_id=self.project.pk))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
