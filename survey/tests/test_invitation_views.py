from http import HTTPStatus

from django.conf import settings
from django.core import mail

import SORT.test.model_factory
import SORT.test.test_case
from SORT.test.model_factory.user.constants import PASSWORD
from survey.services import SurveyService

EMAIL_DATA = dict(email="test@test.com", message="My message")


class InvitationViewTestCase(SORT.test.test_case.ViewTestCase):
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
            consent_config=self.survey.consent_config_default,
            demography_config=self.survey.demography_config_default,
            survey_body_path="Nurses",
        )
        self.invitation = self.service.create_invitation(
            user=self.user, survey=self.survey
        )

    def login_non_member(self):
        """
        Authenticate as a user who isn't a member of the survey's organisation.
        """
        non_member = SORT.test.model_factory.UserFactory()
        self.assertTrue(
            self.client.login(username=non_member.email, password=PASSWORD),
            "Authentication failed",
        )

    def test_invitation_view(self):
        self.get(view_name="invite", pk=self.survey.pk)

    def test_invitation_view_post(self):
        self.post(
            view_name="invite",
            pk=self.survey.pk,
            data=EMAIL_DATA,
            expected_status_code=HTTPStatus.FOUND,
        )
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertIn(f"/survey_response/{self.invitation.token}", body)
        self.assertNotIn("None", body)
        self.assertIn("My message", body)

    def test_invitation_view_anonymous(self):
        response = self.get(
            view_name="invite",
            pk=self.survey.pk,
            login=False,
            expected_status_code=HTTPStatus.FOUND,
        )
        self.assertIn(settings.LOGIN_URL, response.url)

    def test_invitation_view_post_anonymous(self):
        response = self.post(
            view_name="invite",
            pk=self.survey.pk,
            data=EMAIL_DATA,
            login=False,
            expected_status_code=HTTPStatus.FOUND,
        )
        self.assertIn(settings.LOGIN_URL, response.url)
        self.assertEqual(len(mail.outbox), 0)

    def test_invitation_view_non_member(self):
        self.login_non_member()
        self.get(
            view_name="invite",
            pk=self.survey.pk,
            login=False,
            expected_status_code=HTTPStatus.FORBIDDEN,
        )

    def test_invitation_view_post_non_member(self):
        self.login_non_member()
        self.post(
            view_name="invite",
            pk=self.survey.pk,
            data=EMAIL_DATA,
            login=False,
            expected_status_code=HTTPStatus.FORBIDDEN,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_invitation_view_not_found(self):
        self.get(view_name="invite", pk=999999, expected_status_code=HTTPStatus.NOT_FOUND)

    def test_invitation_view_post_not_found(self):
        self.post(
            view_name="invite",
            pk=999999,
            data=EMAIL_DATA,
            expected_status_code=HTTPStatus.NOT_FOUND,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_invitation_view_post_without_invitation(self):
        self.survey.invitation_set.update(used=True)
        response = self.post(view_name="invite", pk=self.survey.pk, data=EMAIL_DATA)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertEqual(len(mail.outbox), 0)
