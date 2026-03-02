from django.db import IntegrityError
from django.test import TestCase

from SORT.test.model_factory import SurveyFactory
from survey.models import SurveyEvidenceSection, Profession


class TestSurveyEvidenceSection(TestCase):
    def setUp(self):
        self.survey = SurveyFactory()
        self.survey.initialise()
        self.survey.save()

    def test_survey_config(self):
        self.assertIsNotNone(self.survey.survey_config)
        self.assertIsInstance(self.survey.survey_config, dict)
        self.assertIsInstance(self.survey.survey_config["sections"], list)

    def test_unique_survey_and_section_index(self):
        """
        Each Survey cannot have more than one section with the same index
        """

        SurveyEvidenceSection.objects.create(survey=self.survey, section_id=0)
        with self.assertRaises(IntegrityError):
            SurveyEvidenceSection.objects.create(survey=self.survey, section_id=0)

    def test_fields(self):
        self.assertIsNotNone(self.survey.fields)
        self.assertTrue(self.survey.fields)

    def test_generate_mock_responses(self):
        self.survey.generate_mock_responses()

        # Check responses aren't empty
        for response in self.survey.survey_response.all():
            self.assertIsNotNone(response.answers)
            self.assertTrue(response.answers)

    def test_generic_profession_configuration(self):
        """
        Test that the Generic profession type loads correct config files
        """
        survey = SurveyFactory(survey_body_path=Profession.GENERIC)
        survey.initialise()
        survey.save()

        # Verify survey was initialized properly
        self.assertIsNotNone(survey.survey_config)
        self.assertIsInstance(survey.survey_config, dict)
        self.assertIsInstance(survey.survey_config["sections"], list)

        # Check that config file paths are correct
        self.assertEqual(survey.template_filename, "sort_only_config_generic.json")
        self.assertEqual(survey.demography_config_filename, "demography_only_config_generic.json")

        # Verify config files can be loaded
        self.assertIsNotNone(survey.sort_config)
        self.assertIsNotNone(survey.demography_config_default)

        # Verify the survey has sections
        self.assertTrue(len(survey.sections) > 0)

        # Verify fields are accessible
        self.assertIsNotNone(survey.fields)
        self.assertTrue(survey.fields)
