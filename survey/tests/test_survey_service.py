"""
Unit tests for the survey service
"""

import json

import django.contrib.auth.models
import django.core.exceptions
import django.test

from home.constants import ROLE_ADMIN
from home.models import Project
from home.services import OrganisationService
from survey.models import Survey, Invitation
from survey.services import SurveyService

User = django.contrib.auth.get_user_model()


class SurveyServiceTestCase(django.test.TestCase):
    def setUp(self):
        organisation_service = OrganisationService()
        self.service = SurveyService()
        self.user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="john.doe@sort-online.org",
        )
        self.anonymous_user = User.objects.create_user(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@sort-online.org",
        )
        self.organisation = organisation_service.create_organisation(
            user=self.user,
            name="Test organisation for survey service tests",
        )
        self.project = Project.objects.create(organisation=self.organisation)

        # Create a survey
        self.survey = Survey.objects.create(project=self.project)
        self.invitation = Invitation.objects.create(survey=self.survey)

        # Save
        self.user.save()
        self.survey.save()
        self.project.save()
        self.organisation.save()

    def test_get_user_role(self):
        role = self.service.get_user_role(user=self.user, survey=self.survey)
        self.assertIsInstance(role, str)
        self.assertEqual(role, ROLE_ADMIN)

    def test_can_view(self):
        self.assertTrue(self.service.can_view(user=self.user, survey=self.survey))

    def test_can_view_unauthorised(self):
        """
        Check that a user that isn't part of the organisation can't view a survey
        """
        self.assertFalse(self.service.can_view(user=self.anonymous_user, survey=self.survey))

    def test_can_edit(self):
        self.assertTrue(self.service.can_edit(user=self.user, survey=self.survey))

    def test_can_edit_unauthorised(self):
        self.assertFalse(self.service.can_edit(user=self.anonymous_user, survey=self.survey))

    def test_can_delete(self):
        self.assertTrue(self.service.can_delete(user=self.user, survey=self.survey))

    def test_can_delete_unauthorised(self):
        self.assertFalse(self.service.can_delete(user=self.anonymous_user, survey=self.survey))

    def test_can_create(self):
        self.assertTrue(self.service.can_create(self.user, self.project))

    def test_can_create_unauthorised(self):
        self.assertFalse(self.service.can_create(self.anonymous_user, self.project))

    def test_get_survey(self):
        self.assertIsInstance(self.survey.pk, int)
        survey = self.service.get_survey(user=self.user, survey_id=self.survey.pk)
        self.assertIsInstance(survey, Survey)
        self.assertEqual(survey.pk, self.survey.pk)

    def test_get_survey_unauthorised(self):
        with self.assertRaises(django.core.exceptions.PermissionDenied):
            self.service.get_survey(user=self.anonymous_user, survey_id=self.survey.pk)

    def test_initialise_survey(self):
        self.service.initialise_survey(user=self.user, project=self.project, survey=self.survey)

        self.assertIsInstance(self.survey.survey_config, dict)
        self.assertIsInstance(self.survey.consent_config, dict)
        self.assertIsInstance(self.survey.survey_config, dict)

    def test_update_consent_demography_config(self):
        self.service.update_consent_demography_config(
            user=self.user,
            survey=self.survey,
            consent_config=dict(sections=list()),
            demography_config=dict(sections=list()),
        )

        self.assertIsInstance(self.survey.survey_config, dict)
        self.assertIsInstance(self.survey.consent_config, dict)
        self.assertIsInstance(self.survey.survey_config, dict)

    def test_get_survey_from_token(self):
        token = self.survey.current_invite_token()
        self.assertIsInstance(token, str)
        survey = self.service.get_survey_from_token(token=token)
        self.assertIsInstance(survey, Survey)

    def test_accept_response(self):
        self.service.accept_response(survey=self.survey, responseValues=json.dumps("[]"))
        self.assertTrue(self.survey.survey_response.exists())

    def test_create_invitation(self):
        self.service.create_invitation(user=self.user, survey=self.survey)
        self.service.create_invitation(user=self.user, survey=self.survey)
        invitation = self.service.create_invitation(user=self.user, survey=self.survey)
        self.assertIsInstance(invitation, Invitation)

        # The old invitations should be expired, except for the latest one
        # True, True, True, False
        used_values = tuple(self.survey.invitation_set.values_list('used', flat=True))
        for used in used_values[:-1]:
            self.assertTrue(used)
        self.assertFalse(used_values[-1])

    def test_export_csv(self):
        csv_data = self.service.export_csv(user=self.user, survey=self.survey)
        self.assertIsInstance(csv_data, str)
