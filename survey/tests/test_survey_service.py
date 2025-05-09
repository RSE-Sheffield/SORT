"""
Unit tests for the survey service
"""

import json

import django.contrib.auth.models
import django.core.exceptions
import django.test

import SORT.test.model_factory
import SORT.test.test_case
from home.constants import ROLE_ADMIN
from survey.models import Invitation, Survey
from survey.services import SurveyService


class SurveyServiceTestCase(SORT.test.test_case.ServiceTestCase):
    def setUp(self):
        self.client = django.test.Client()
        self.service = SurveyService()
        self.invitation = SORT.test.model_factory.InvitationFactory()
        self.survey = self.invitation.survey
        self.project = self.survey.project
        self.organisation = self.project.organisation
        self.admin = self.organisation.members.first()
        self.anonymous_user = SORT.test.model_factory.UserFactory()

    def test_get_user_role(self):
        role = self.service.get_user_role(user=self.admin, survey=self.survey)
        self.assertIsInstance(role, str)
        self.assertEqual(role, ROLE_ADMIN)

    def test_can_view(self):
        self.assertTrue(self.service.can_view(user=self.admin, survey=self.survey))

    def test_can_view_unauthorised(self):
        """
        Check that a user that isn't part of the organisation can't view a survey
        """
        self.assertFalse(
            self.service.can_view(user=self.anonymous_user, survey=self.survey)
        )

    def test_can_edit(self):
        self.assertTrue(self.service.can_edit(user=self.admin, survey=self.survey))

    def test_can_edit_unauthorised(self):
        self.assertFalse(
            self.service.can_edit(user=self.anonymous_user, survey=self.survey)
        )

    def test_can_delete(self):
        self.assertTrue(self.service.can_delete(user=self.admin, survey=self.survey))

    def test_can_delete_unauthorised(self):
        self.assertFalse(
            self.service.can_delete(user=self.anonymous_user, survey=self.survey)
        )

    def test_can_create(self):
        self.assertTrue(self.service.can_create(self.admin, self.project))

    def test_can_create_unauthorised(self):
        self.assertFalse(self.service.can_create(self.anonymous_user, self.project))

    def test_get_survey(self):
        self.assertIsInstance(self.survey.pk, int)
        survey = self.service.get_survey(user=self.admin, survey_id=self.survey.pk)
        self.assertIsInstance(survey, Survey)
        self.assertEqual(survey.pk, self.survey.pk)

    def test_get_survey_unauthorised(self):
        with self.assertRaises(django.core.exceptions.PermissionDenied):
            self.service.get_survey(user=self.anonymous_user, survey_id=self.survey.pk)

    def test_initialise_survey(self):
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )

        self.assertIsInstance(self.survey.survey_config, dict)
        self.assertIsInstance(self.survey.consent_config, dict)
        self.assertIsInstance(self.survey.survey_config, dict)

        # Check that a blank survey was created
        self.assertEqual(len(self.survey.survey_config["sections"]), 0)

    def test_update_consent_demography_config(self):
        self.service.update_consent_demography_config(
            user=self.admin,
            survey=self.survey,
            consent_config=dict(sections=list()),
            demography_config=dict(sections=list()),
            survey_body_path="Nurses",
        )

        self.assertIsInstance(self.survey.survey_config, dict)
        self.assertIsInstance(self.survey.consent_config, dict)
        self.assertIsInstance(self.survey.survey_config, dict)

        # There should be some SORT survey sections
        self.assertGreater(
            len(self.survey.survey_config["sections"]), 0, "No survey sections"
        )
        # There shouldn't be any consent or demography since we updated with empty values above
        self.assertEqual(
            len(self.survey.consent_config["sections"]),
            0,
            "Unexpected consent sections",
        )
        self.assertEqual(
            len(self.survey.demography_config["sections"]),
            0,
            "Unexpected demography sections",
        )

    def test_get_survey_from_token(self):
        token = self.survey.current_invite_token()
        self.assertIsInstance(token, str)
        survey = self.service.get_survey_from_token(token=token)
        self.assertIsInstance(survey, Survey)

    def test_accept_response(self):
        self.service.accept_response(
            survey=self.survey, responseValues=json.dumps("[]")
        )
        self.assertTrue(self.survey.survey_response.exists())

    def test_create_invitation(self):
        self.service.create_invitation(user=self.admin, survey=self.survey)
        self.service.create_invitation(user=self.admin, survey=self.survey)
        invitation = self.service.create_invitation(user=self.admin, survey=self.survey)
        self.assertIsInstance(invitation, Invitation)

        # The old invitations should be expired, except for the latest one
        # True, True, True, False
        used_values = tuple(self.survey.invitation_set.values_list("used", flat=True))
        for used in used_values[:-1]:
            self.assertTrue(used)
        self.assertFalse(used_values[-1])

    def test_export_csv(self):
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )
        csv_data = self.service.export_csv(user=self.admin, survey=self.survey)
        self.assertIsInstance(csv_data, str)

    def test_mock_responses(self):
        self.skipTest("Not yet implemented")
        self.service.generate_mock_responses(
            user=self.admin, survey=self.survey, num_responses=3
        )

    def test_create_survey_evidence_sections(self):
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )
        self.service.update_consent_demography_config(
            user=self.admin,
            survey=self.survey,
            consent_config=self.survey.consent_config,
            demography_config=self.survey.demography_config,
            survey_body_path="Nurses",
        )
        # from survey.models import SurveyEvidenceSection
        # evidence_sections = SurveyEvidenceSection.objects.filter(survey=self.survey).order_by("section_id")
        # self.assertEqual(evidence_sections.count(), len(self.survey.survey_config["sections"]))
        self.assertGreater(self.survey.evidence_sections.count(), 0)
        sort_sections = [
            section
            for section in self.survey.survey_config["sections"]
            if section["type"] == "sort"
        ]
        self.assertEqual(self.survey.evidence_sections.count(), len(sort_sections))
