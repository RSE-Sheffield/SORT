import os
from http import HTTPStatus
import secrets

import django.test
import django.urls
import django.contrib.auth

from home.models import Project, Organisation
from home.services import OrganisationService
from survey.services import SurveyService
from survey.models import Survey, Invitation

User = django.contrib.auth.get_user_model()

PASSWORD = secrets.token_urlsafe()


class SurveyServiceTestCase(django.test.TestCase):
    def setUp(self):
        # Initialise environment
        self.user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="john.doe@sort-online.org",
            password=PASSWORD,
        )
        organisation = OrganisationService().create_organisation(user=self.user, name="Survey test org")
        project = Project.objects.create(organisation=organisation)

        # Create survey
        self.survey = Survey.objects.create()
        SurveyService().initialise_survey(user=self.user, project=project, survey=self.survey)

    def login(self):
        self.assertTrue(self.client.login(username=self.user.email, password=PASSWORD))

    def get(self, view_name: str, expected_status_code: int = HTTPStatus.OK, login: bool = True, **kwargs):
        if login:
            self.login()
        response = self.client.get(django.urls.reverse(view_name, kwargs=kwargs))
        self.assertEqual(response.status_code, expected_status_code)
        return response

    def post(self, view_name: str, expected_status_code: int = HTTPStatus.OK, login: bool = True, **kwargs):
        if login:
            self.login()
        response = self.client.post(django.urls.reverse(view_name, kwargs=kwargs))
        self.assertEqual(response.status_code, expected_status_code)
        return response

    def test_survey_get(self):
        self.get("survey", pk=self.survey.pk)

    def test_survey_get_unauthorised(self):
        # Redirect to login page (302)
        self.get("survey", expected_status_code=HTTPStatus.NOT_FOUND, login=False, pk=self.survey.pk)

    def test_survey_post(self):
        self.post("survey", pk=self.survey.pk)

    def test_survey_create_get(self):
        self.get("survey_create", project_id=self.survey.project.pk)

    def test_survey_create_post(self):
        self.post("survey_create", project_id=self.survey.project.pk)

    def test_survey_delete_get(self):
        self.get("survey_delete", pk=self.survey.pk)

    def test_survey_delete_post(self):
        # We expect a 302 redirect after deletion
        self.post("survey_delete", pk=self.survey.pk, expected_status_code=HTTPStatus.FOUND)

    def test_survey_configure_get(self):
        self.get("survey_configure", pk=self.survey.pk)

    def test_survey_configure_post(self):
        self.post("survey_configure", pk=self.survey.pk)

    def test_survey_export(self):
        self.get("survey_export", pk=self.survey.pk)

    def test_survey_improvement_plan(self):
        self.get("survey_improvement_plan", pk=self.survey.pk)

    def test_survey_evidence_gathering(self):
        self.get("survey_evidence_gathering", pk=self.survey.pk)

    def test_survey_response_get(self):
        invitation = Invitation.objects.create(survey=self.survey)
        self.get("survey_response", token=invitation.token)

    def test_survey_response_post(self):
        invitation = Invitation.objects.create(survey=self.survey)
        self.post("survey_response", token=invitation.token)

    def test_survey_link_invalid(self):
        self.get("survey_link_invalid")

    def test_success_invitation(self):
        self.skipTest("https://github.com/RSE-Sheffield/SORT/pull/170#issuecomment-2740200064")
        self.get("success_invitation")
