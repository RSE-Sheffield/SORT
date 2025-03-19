import django.test
import django.contrib.auth.models
from survey.services import SurveyService

from survey.models import Survey


class SurveyServiceTestCase(django.test.TestCase):
    def setUp(self):
        self.service = SurveyService()

    def test_can_view(self):
        """
        Anonymous user can view a survey
        """
        anonymous_user = django.contrib.auth.models.AnonymousUser()
        self.assertTrue(self.service.can_view(user=anonymous_user, survey=Survey.objects.create()))
