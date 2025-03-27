"""
Test the project service
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

import SORT.test.test_case
from home.models import Project
from home.services import OrganisationService, ProjectService

from .constants import PASSWORD

User = get_user_model()


class ProjectServiceTestCase(SORT.test.test_case.ServiceTestCase):

    def setUp(self):
        self.service = ProjectService()

        # Create fake users for testing purposes
        self.user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="john.doe@sort-online.org",
            password=PASSWORD,
        )
        self.superuser = User.objects.create_superuser(
            first_name="Janet",
            last_name="Smith",
            email="janet.smith@sort-online.org",
            password=PASSWORD,
        )

        self.organisation = OrganisationService().create_organisation(
            user=self.superuser,
            name="Test Organisation",
            description="Test Organisation",
        )

    def test_create_project_permission_denied(self):
        """
        Test that a normal user can't create projects
        """

        # This should raise a permission denied error
        self.assertRaises(
            PermissionDenied,
            self.service.create_project,
            user=self.user,
            name="Testing Project",
            description="Testing Project",
            organisation=self.organisation,
        )

    def test_create_project(self):
        user = self.superuser
        name = "Testing Project"

        self.service.create_project(
            user=user,
            name="Testing Project",
            description="Testing Project",
            organisation=self.organisation,
        )

        # Ensure it worked and we created a new org.
        self.assertTrue(Project.objects.exists(), "No project was created")
        self.assertEqual(Project.objects.count(), 1, "Unexpected number of projects")

        project = Project.objects.first()

        self.assertEqual(project.name, name, "Unexpected project name")
