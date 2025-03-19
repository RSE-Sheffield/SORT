import django.test
import django.contrib.auth.models
from survey.services import SurveyService

from survey.models import Survey


class SurveyServiceTestCase(django.test.TestCase):
    def setUp(self):
        self.service = SurveyService()
        self.survey = Survey.objects.create()

    def test_anonymous_view(self):
        """
        Anonymous user can't view a survey
        """
        anonymous_user = django.contrib.auth.models.AnonymousUser()

        self.assertFalse(self.service.can_view(user=anonymous_user, survey=self.survey))

    def test_user_can_view(self):
        """
        A user in that organisation can view a survey
        """

        pass
