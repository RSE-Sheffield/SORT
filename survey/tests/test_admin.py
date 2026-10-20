"""
Survey answers are stored by position, so the Django admin must not allow the
question configuration to change once a survey has responses.
"""

from django.contrib import admin
from django.test import RequestFactory, TestCase

from SORT.test.model_factory import SurveyFactory
from survey.admin import SurveyAdmin
from survey.models import Survey, SurveyResponse


class SurveyAdminTestCase(TestCase):
    def setUp(self):
        self.survey = SurveyFactory()
        self.survey.initialise()
        self.survey.save()
        self.model_admin = SurveyAdmin(Survey, admin.site)
        self.request = RequestFactory().get("/")

    def test_config_editable_without_responses(self):
        readonly = self.model_admin.get_readonly_fields(self.request, self.survey)
        self.assertNotIn("survey_config", readonly)

    def test_config_readonly_with_responses(self):
        SurveyResponse.objects.create(survey=self.survey, answers=self.survey._generate_mock_response())
        readonly = self.model_admin.get_readonly_fields(self.request, self.survey)
        self.assertIn("survey_config", readonly)
