from django.db import IntegrityError
from django.test import TestCase
from home.models import Project, Organisation
from home.tests.model_factory import SurveyFactory
from survey.models import Survey, SurveyEvidenceSection

class TestSurveyEvidenceSection(TestCase):

    def test_unique_survey_and_section_index(self):
        """
        Each Survey cannot have more than one section with the same index
        """

        survey = SurveyFactory()
        SurveyEvidenceSection.objects.create(survey=survey, section_id=0)
        with self.assertRaises(IntegrityError):
            SurveyEvidenceSection.objects.create(survey=survey, section_id=0)
