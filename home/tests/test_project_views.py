"""
Test project views
"""

import SORT.test.test_case
import django.urls

from SORT.test.model_factory import ProjectFactory, SurveyFactory


class ProjectViewTestCase(SORT.test.test_case.ViewTestCase):

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()
        self.user = self.project.organisation.members.first()

    def test_project_detail_view(self):
        self.get("project", project_id=self.project.pk)

    def test_sharing_links_shown_for_shared_survey(self):
        SurveyFactory(project=self.project, is_shared=True)
        response = self.get("project", project_id=self.project.pk)
        self.assertContains(response, django.urls.reverse("participant_information"))
        self.assertContains(response, django.urls.reverse("data_sharing_agreement"))

    def test_sharing_links_hidden_for_unshared_survey(self):
        SurveyFactory(project=self.project, is_shared=False)
        response = self.get("project", project_id=self.project.pk)
        self.assertNotContains(
            response, django.urls.reverse("participant_information")
        )
        self.assertNotContains(
            response, django.urls.reverse("data_sharing_agreement")
        )

    def test_project_edit_view(self):
        self.skipTest("Not implemented")

    def test_project_create_view(self):
        self.skipTest("Not implemented")

    def test_project_delete_view(self):
        self.skipTest("Not implemented")
