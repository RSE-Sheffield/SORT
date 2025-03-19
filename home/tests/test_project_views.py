"""
Test project views
"""

from http import HTTPStatus

import django.test
import django.urls
from django.contrib.auth import get_user_model

from home.services import OrganisationService, ProjectService

from .constants import PASSWORD

User = get_user_model()


class ProjectViewTestCase(django.test.TestCase):

    def setUp(self):
        self.project_service = ProjectService()
        self.organisation_service = OrganisationService()
        self.superuser = User.objects.create_superuser(
            first_name='John',
            last_name='Smith',
            email='john.smith@sheffield.ac.uk',
            password=PASSWORD,
        )
        self.organisation = self.organisation_service.create_organisation(
            user=self.superuser,
            name="My organisation",
            description="This is an org.",
        )
        self.project = self.project_service.create_project(
            user=self.superuser,
            name="My test project",
            organisation=self.organisation
        )

    def login(self):
        self.assertTrue(self.client.login(username=self.user.email, password=PASSWORD))

    def login_superuser(self):
        self.assertTrue(self.client.login(username=self.superuser.email, password=PASSWORD))

    def test_projects_detail_view(self):
        self.login_superuser()
        response = self.client.get(django.urls.reverse("project", kwargs=dict(project_id=self.project.pk)))
        self.assertEqual(response.status_code, HTTPStatus.OK)
