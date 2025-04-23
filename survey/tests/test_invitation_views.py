from http import HTTPStatus

import SORT.test.model_factory
import SORT.test.test_case
from survey.models import Invitation
from survey.services import SurveyService


class SurveyServiceTestCase(SORT.test.test_case.ViewTestCase):
    def setUp(self):
        super().setUp()
        self.service = SurveyService()
        self.survey = SORT.test.model_factory.SurveyFactory()
        self.project = self.survey.project
        self.organisation = self.project.organisation
        self.user = self.organisation.members.first()
        self.service.initialise_survey(
            user=self.user, project=self.project, survey=self.survey
        )
        self.service.update_consent_demography_config(
            user=self.user,
            survey=self.survey,
            consent_config=self.survey.consent_config,
            demography_config=self.survey.demography_config,
            survey_body_path="Nurse",
        )

    def test_invitation_view(self):
        self.get(view_name="invite", pk=self.survey.pk)

    def test_invitation_view_post(self):
        self.post(
            view_name="invite", pk=self.survey.pk,
            data=dict(email="test@test.com", message="My message"),
            # Expect redirection on success
            expected_status_code=HTTPStatus.FOUND
        )
