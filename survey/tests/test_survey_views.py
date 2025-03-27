from http import HTTPStatus

import django.contrib.auth

import SORT.test.test_case
from home.models import Project
from home.services import OrganisationService
from survey.models import Invitation, Survey
from survey.services import SurveyService

User = django.contrib.auth.get_user_model()


class SurveyServiceTestCase(SORT.test.test_case.ViewTestCase):
    def setUp(self):
        super().setUp()
        organisation = OrganisationService().create_organisation(
            user=self.user, name="Survey test org"
        )
        project = Project.objects.create(organisation=organisation)

        # Create survey
        self.survey = Survey.objects.create()
        SurveyService().initialise_survey(
            user=self.user, project=project, survey=self.survey
        )

    def test_survey_get(self):
        self.get("survey", pk=self.survey.pk)

    def test_survey_get_unauthorised(self):
        # Redirect to login page (302)
        self.get(
            "survey",
            expected_status_code=HTTPStatus.FOUND,
            login=False,
            pk=self.survey.pk,
        )

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
        self.post(
            "survey_delete", pk=self.survey.pk, expected_status_code=HTTPStatus.FOUND
        )

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
        self.skipTest(
            "https://github.com/RSE-Sheffield/SORT/pull/170#issuecomment-2740200064"
        )
        self.get("success_invitation")
