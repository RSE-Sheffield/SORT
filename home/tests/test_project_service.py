"""
Test the project service
"""

from django.core.exceptions import PermissionDenied

import SORT.test.test_case
from home.models import Project
from home.services import ProjectService
from SORT.test.model_factory import OrganisationFactory


class ProjectServiceTestCase(SORT.test.test_case.ServiceTestCase):

    def setUp(self):
        super().setUp()
        self.service = ProjectService()
        self.organisation = OrganisationFactory()
        self.admin = self.organisation.members.first()

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
        user = self.admin
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
