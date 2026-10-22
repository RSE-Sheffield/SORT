"""
Tests for audit logging (sort.audit logger) of project events
"""

import SORT.test.test_case
from home.services import project_service
from SORT.test.model_factory import OrganisationFactory


class ProjectAuditLogTestCase(SORT.test.test_case.ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory()
        self.admin = self.organisation.members.first()

    def test_create_and_delete_project_logs(self):
        with self.assertLogs("sort.audit", level="INFO") as logs:
            project = project_service.create_project(
                user=self.admin, name="Testing Project", organisation=self.organisation
            )
        message = logs.records[0].getMessage()
        self.assertIn("project created", message)
        self.assertIn(f"project_id={project.pk}", message)
        self.assertIn(f"user_id={self.admin.pk}", message)
        self.assertNotIn("Testing Project", message)

        with self.assertLogs("sort.audit", level="INFO") as logs:
            project_service.delete_project(self.admin, project)
        self.assertIn("project deleted", logs.records[0].getMessage())
