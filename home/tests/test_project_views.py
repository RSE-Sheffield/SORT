"""
Test project views
"""

import SORT.test.test_case
from SORT.test.model_factory import ProjectFactory


class ProjectViewTestCase(SORT.test.test_case.ViewTestCase):

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()
        self.user = self.project.organisation.members.first()

    def test_project_detail_view(self):
        self.get("project", project_id=self.project.pk)

    def test_project_edit_view(self):
        self.skipTest("Not implemented")

    def test_project_create_view(self):
        self.skipTest("Not implemented")

    def test_project_delete_view(self):
        self.skipTest("Not implemented")
