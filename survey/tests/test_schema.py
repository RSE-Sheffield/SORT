import copy

from django.core.exceptions import ValidationError
from django.test import TestCase

from SORT.test.model_factory import SurveyFactory
from survey.models import SurveyResponse


class TestResponseSchema(TestCase):
    def setUp(self):
        self.survey = SurveyFactory()
        self.survey.initialise()
        self.survey.save()

    def test_schema_generated(self):
        schema = self.survey.response_schema
        self.assertEqual(schema["type"], "array")
        self.assertEqual(
            schema["minItems"], len(self.survey.sections)
        )

    def test_valid_mock_response_passes(self):
        answers = self.survey._generate_mock_response()
        response = SurveyResponse(survey=self.survey, answers=answers)
        response.clean()

    def test_wrong_number_of_sections(self):
        answers = self.survey._generate_mock_response()
        answers.pop()  # Remove last section
        response = SurveyResponse(survey=self.survey, answers=answers)
        with self.assertRaises(ValidationError):
            response.clean()

    def test_wrong_number_of_fields(self):
        answers = self.survey._generate_mock_response()
        answers[0].pop()  # Remove last field from first section
        response = SurveyResponse(survey=self.survey, answers=answers)
        with self.assertRaises(ValidationError):
            response.clean()

    def test_extra_section_rejected(self):
        answers = self.survey._generate_mock_response()
        answers.append(["extra"])
        response = SurveyResponse(survey=self.survey, answers=answers)
        with self.assertRaises(ValidationError):
            response.clean()

    def test_invalid_likert_value(self):
        answers = self.survey._generate_mock_response()
        # Find the first section whose first field is a likert
        likert_section_index = next(
            i for i, section in enumerate(self.survey.sections)
            if section.get("fields") and section["fields"][0]["type"] == "likert"
        )
        answers[likert_section_index][0] = copy.deepcopy(answers[likert_section_index][0])
        answers[likert_section_index][0][0] = "99"  # Invalid value
        response = SurveyResponse(survey=self.survey, answers=answers)
        with self.assertRaises(ValidationError):
            response.clean()

    def test_wrong_likert_sublabel_count(self):
        answers = self.survey._generate_mock_response()
        likert_section_index = next(
            i for i, section in enumerate(self.survey.sections)
            if section.get("fields") and section["fields"][0]["type"] == "likert"
        )
        answers[likert_section_index][0] = ["0"]  # Only 1 instead of expected count
        response = SurveyResponse(survey=self.survey, answers=answers)
        with self.assertRaises(ValidationError):
            response.clean()

    def test_required_checkbox_empty(self):
        answers = self.survey._generate_mock_response()
        # Consent section (index 0) has required checkboxes
        answers[0][0] = []  # Empty required checkbox
        response = SurveyResponse(survey=self.survey, answers=answers)
        with self.assertRaises(ValidationError):
            response.clean()
