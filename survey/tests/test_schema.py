import copy

import jsonschema
from django.core.exceptions import ValidationError
from django.test import TestCase

from SORT.test.model_factory import SurveyFactory
from survey.models import SurveyResponse
from survey.schema import (
    _checkbox_schema,
    _likert_schema,
    _radio_schema,
    _text_schema,
    field_schema,
)


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


class TestFieldSchema(TestCase):
    """Unit tests for individual schema-generation functions in survey/schema.py."""

    LIKERT_CONFIG = {
        "type": "likert",
        "sublabels": ["Q1", "Q2", "Q3"],
        "options": ["0", "1", "2", "3", "4"],
    }
    RADIO_CONFIG = {
        "type": "radio",
        "options": ["Yes", "No", "Maybe"],
    }
    CHECKBOX_CONFIG = {
        "type": "checkbox",
        "options": ["A", "B", "C"],
    }
    TEXT_CONFIG = {"type": "text"}

    # --- likert ---

    def test_likert_schema_structure(self):
        schema = _likert_schema(self.LIKERT_CONFIG)
        self.assertEqual(schema["type"], "array")
        self.assertEqual(schema["minItems"], 3)
        self.assertEqual(schema["maxItems"], 3)
        self.assertEqual(schema["items"]["enum"], ["0", "1", "2", "3", "4"])

    def test_likert_schema_valid_value(self):
        schema = _likert_schema(self.LIKERT_CONFIG)
        jsonschema.validate(["0", "2", "4"], schema)  # Should not raise

    def test_likert_schema_invalid_value(self):
        schema = _likert_schema(self.LIKERT_CONFIG)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(["0", "99", "4"], schema)

    def test_likert_schema_wrong_length(self):
        schema = _likert_schema(self.LIKERT_CONFIG)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(["0"], schema)

    # --- radio ---

    def test_radio_schema_structure(self):
        schema = _radio_schema(self.RADIO_CONFIG)
        self.assertEqual(schema["type"], "string")
        self.assertEqual(schema["enum"], ["Yes", "No", "Maybe"])

    def test_radio_schema_valid_value(self):
        schema = _radio_schema(self.RADIO_CONFIG)
        jsonschema.validate("Yes", schema)  # Should not raise

    def test_radio_schema_invalid_value(self):
        schema = _radio_schema(self.RADIO_CONFIG)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate("Other", schema)

    def test_radio_schema_required_minlength(self):
        config = {**self.RADIO_CONFIG, "required": True}
        schema = _radio_schema(config)
        self.assertEqual(schema["minLength"], 1)

    def test_radio_schema_not_required_no_minlength(self):
        schema = _radio_schema(self.RADIO_CONFIG)
        self.assertNotIn("minLength", schema)

    # --- select (dispatched same as radio) ---

    def test_select_schema_same_as_radio(self):
        radio_config = {**self.RADIO_CONFIG}
        select_config = {**self.RADIO_CONFIG, "type": "select"}
        self.assertEqual(field_schema(radio_config), field_schema(select_config))

    # --- checkbox ---

    def test_checkbox_schema_structure(self):
        schema = _checkbox_schema(self.CHECKBOX_CONFIG)
        self.assertEqual(schema["type"], "array")
        self.assertEqual(schema["items"]["enum"], ["A", "B", "C"])

    def test_checkbox_schema_valid_value(self):
        schema = _checkbox_schema(self.CHECKBOX_CONFIG)
        jsonschema.validate(["A", "C"], schema)  # Should not raise

    def test_checkbox_schema_invalid_value(self):
        schema = _checkbox_schema(self.CHECKBOX_CONFIG)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(["A", "Z"], schema)

    def test_checkbox_schema_required_min_items(self):
        config = {**self.CHECKBOX_CONFIG, "required": True}
        schema = _checkbox_schema(config)
        self.assertEqual(schema["minItems"], 1)

    def test_checkbox_schema_not_required_no_min_items(self):
        schema = _checkbox_schema(self.CHECKBOX_CONFIG)
        self.assertNotIn("minItems", schema)

    # --- text / textarea ---

    def test_text_schema_structure(self):
        schema = _text_schema(self.TEXT_CONFIG)
        self.assertEqual(schema["type"], "string")

    def test_text_schema_required_minlength(self):
        config = {**self.TEXT_CONFIG, "required": True}
        schema = _text_schema(config)
        self.assertEqual(schema["minLength"], 1)

    def test_textarea_schema_same_as_text(self):
        text_config = {**self.TEXT_CONFIG}
        textarea_config = {**self.TEXT_CONFIG, "type": "textarea"}
        self.assertEqual(field_schema(text_config), field_schema(textarea_config))

    # --- unknown type ---

    def test_unknown_field_type_returns_empty_schema(self):
        schema = field_schema({"type": "unknown_widget"})
        self.assertEqual(schema, {})


class TestSurveyResponseValidate(TestCase):
    """Integration tests for SurveyResponse.validate() using minimal survey configs."""

    def _make_survey(self, sections, is_active=True):
        survey = SurveyFactory()
        survey.survey_config = {"sections": sections}
        survey.is_active = is_active
        survey.save()
        return survey

    def _response(self, survey, answers):
        return SurveyResponse(survey=survey, answers=answers)

    # --- radio ---

    def test_radio_valid_answer_passes(self):
        survey = self._make_survey([
            {"fields": [{"type": "radio", "options": ["Yes", "No"]}]}
        ])
        self._response(survey, [["Yes"]]).validate()  # Should not raise

    def test_radio_invalid_answer_raises(self):
        survey = self._make_survey([
            {"fields": [{"type": "radio", "options": ["Yes", "No"]}]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [["Maybe"]]).validate()

    # --- required text ---

    def test_required_text_empty_raises(self):
        survey = self._make_survey([
            {"fields": [{"type": "text", "required": True}]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [[""]]).validate()

    def test_required_text_valid_passes(self):
        survey = self._make_survey([
            {"fields": [{"type": "text", "required": True}]}
        ])
        self._response(survey, [["some text"]]).validate()  # Should not raise

    # --- checkbox ---

    def test_checkbox_invalid_option_raises(self):
        survey = self._make_survey([
            {"fields": [{"type": "checkbox", "options": ["A", "B"]}]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [[["Z"]]]).validate()

    # --- validate() vs clean() and inactive survey ---

    def test_validate_does_not_check_inactive_survey(self):
        survey = self._make_survey(
            [{"fields": [{"type": "text"}]}],
            is_active=False,
        )
        # validate() checks schema only — inactive status is irrelevant
        self._response(survey, [["any value"]]).validate()  # Should not raise

    def test_clean_rejects_inactive_survey(self):
        survey = self._make_survey(
            [{"fields": [{"type": "text"}]}],
            is_active=False,
        )
        with self.assertRaises(ValidationError):
            self._response(survey, [["any value"]]).clean()
