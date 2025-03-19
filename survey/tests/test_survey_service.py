"""
Unit tests for the survey service
"""

import django.test
import django.contrib.auth.models

from survey.services import SurveyService
from home.models import Project, Organisation, OrganisationMembership
from survey.models import Survey
from home.services import OrganisationService

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
        self.organisation = organisation_service.create_organisation(
            user=self.user,
            name="Test organisation for survey service tests",
        )
        self.project = Project.objects.create(organisation=self.organisation)

        # Create a survey
        self.survey = Survey.objects.create()
        self.survey.project = self.project

    def test_can_view_unauthorised(self):
        """
        Check that a user that isn't part of the organisation can't view a survey
        """
        anonymous_user = User.objects.create_user(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@sort-online.org",
        )

        self.assertFalse(self.service.can_view(user=anonymous_user, survey=self.survey))

    def test_user_can_view(self):
        """
        A user in that organisation can view a survey
        """

        self.assertTrue(self.service.can_view(user=self.user, survey=self.survey))

    def test_get_user_role(self):
        self.service.get_user_role(self.user, self.survey)

    def test_can_view(self):
        self.service.can_view(self.user, self.survey)
