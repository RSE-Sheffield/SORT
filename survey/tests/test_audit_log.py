"""
Tests for audit logging (sort.audit logger) of survey events
"""

import django.urls
from django.core.exceptions import PermissionDenied

import SORT.test.model_factory
import SORT.test.test_case
from survey.models import Survey
from survey.services import SurveyService


class SurveyAuditLogTestCase(SORT.test.test_case.ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.service = SurveyService()
        self.invitation = SORT.test.model_factory.InvitationFactory()
        self.survey = self.invitation.survey
        self.project = self.survey.project
        self.admin = self.project.organisation.members.first()

    def assert_audit(self, logs, text):
        self.assertEqual(len(logs.records), 1)
        message = logs.records[0].getMessage()
        self.assertIn(text, message)
        self.assertIn(f"user_id={self.admin.pk}", message)
        self.assertIn(self.admin.email, message)
        return message

    def test_initialise_survey_logs(self):
        survey = Survey(name="Secret name")
        with self.assertLogs("sort.audit", level="INFO") as logs:
            self.service.initialise_survey(self.admin, self.project, survey)
        message = self.assert_audit(logs, "survey created")
        self.assertIn(f"survey_id={survey.pk}", message)
        self.assertNotIn("Secret name", message)

    def test_delete_survey_logs(self):
        survey_id = self.survey.pk
        with self.assertLogs("sort.audit", level="INFO") as logs:
            self.service.delete_survey(self.admin, self.survey)
        message = self.assert_audit(logs, "survey deleted")
        self.assertIn(f"survey_id={survey_id}", message)
        self.assertFalse(Survey.objects.filter(pk=survey_id).exists())

    def test_delete_survey_unauthorised_no_log(self):
        other = SORT.test.model_factory.UserFactory()
        with self.assertNoLogs("sort.audit", level="INFO"):
            with self.assertRaises(PermissionDenied):
                self.service.delete_survey(other, self.survey)

    def test_rename_via_view_logs(self):
        self.client.force_login(self.admin)
        with self.assertLogs("sort.audit", level="INFO") as logs:
            self.client.post(
                django.urls.reverse("survey_edit", kwargs={"pk": self.survey.pk}),
                {"name": "New name", "description": ""},
            )
        self.assert_audit(logs, "survey renamed")
