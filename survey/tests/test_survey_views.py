import json
from http import HTTPStatus

import SORT.test.model_factory
import SORT.test.test_case
from survey.models import Invitation, Profession
from survey.services import SurveyService


class SurveyViewTestCase(SORT.test.test_case.ViewTestCase):
    def setUp(self):
        super().setUp()
        self.service = SurveyService()
        self.survey = SORT.test.model_factory.SurveyFactory()
        self.project = self.survey.project
        self.organisation = self.project.organisation
        self.user = self.organisation.members.first()
        self.survey.initialise()
        self.survey.save()

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
        self.post(
            view_name="survey_configure",
            pk=self.survey.pk,
            data=dict(
                consent_config=json.dumps(self.survey.consent_config_default),
                demography_config=json.dumps(self.survey.demography_config_default),
            ),
            expected_status_code=HTTPStatus.FOUND,
        )

    def test_survey_export(self):
        self.get("survey_export", pk=self.survey.pk)

    def test_survey_improvement_plan(self):
        # Test sections A to E
        for improvement_section in self.survey.improvement_sections.all():
            with self.subTest(section_id=improvement_section.section_id):
                self.get(
                    view_name="survey_improvement_plan",
                    pk=self.survey.pk,
                    section_id=improvement_section.section_id,
                )

    def test_survey_evidence_gathering(self):
        # Test sections A to E
        for evidence_section in self.survey.evidence_sections.all():
            with self.subTest(section_id=evidence_section.section_id):
                self.get(
                    "survey_evidence_gathering",
                    pk=self.survey.pk,
                    section_id=evidence_section.section_id,
                )

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
