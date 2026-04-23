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

    def test_radio_wrong_json_type_rejected(self):
        survey = self._make_survey([
            {"fields": [{"type": "radio", "options": ["Yes", "No"]}]}
        ])
        for bad in (["Yes"], 1, None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    self._response(survey, [[bad]]).validate()

    def test_required_radio_empty_string_rejected(self):
        survey = self._make_survey([
            {"fields": [{"type": "radio", "options": ["Yes", "No"], "required": True}]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [[""]]).validate()

    def test_radio_without_options_accepts_any_string(self):
        survey = self._make_survey([
            {"fields": [{"type": "radio"}]}
        ])
        self._response(survey, [["anything"]]).validate()  # Should not raise

    # --- select ---

    def test_select_valid_answer_passes(self):
        survey = self._make_survey([
            {"fields": [{"type": "select", "options": ["A", "B"]}]}
        ])
        self._response(survey, [["A"]]).validate()  # Should not raise

    def test_select_invalid_answer_raises(self):
        survey = self._make_survey([
            {"fields": [{"type": "select", "options": ["A", "B"]}]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [["C"]]).validate()

    # --- checkbox ---

    def test_checkbox_invalid_option_raises(self):
        survey = self._make_survey([
            {"fields": [{"type": "checkbox", "options": ["A", "B"]}]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [[["Z"]]]).validate()

    def test_checkbox_wrong_json_type_rejected(self):
        survey = self._make_survey([
            {"fields": [{"type": "checkbox", "options": ["A", "B"]}]}
        ])
        for bad in ("A", None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    self._response(survey, [[bad]]).validate()

    def test_checkbox_non_string_item_rejected(self):
        survey = self._make_survey([
            {"fields": [{"type": "checkbox", "options": ["A", "B"]}]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [[[1]]]).validate()

    def test_required_checkbox_empty_array_rejected(self):
        survey = self._make_survey([
            {"fields": [{"type": "checkbox", "options": ["A", "B"], "required": True}]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [[[]]]).validate()

    def test_optional_checkbox_empty_array_accepted(self):
        survey = self._make_survey([
            {"fields": [{"type": "checkbox", "options": ["A", "B"]}]}
        ])
        self._response(survey, [[[]]]).validate()  # Should not raise

    def test_checkbox_without_options_accepts_any_strings(self):
        survey = self._make_survey([
            {"fields": [{"type": "checkbox"}]}
        ])
        self._response(survey, [[["anything", "else"]]]).validate()  # Should not raise

    # --- text ---

    def test_text_wrong_json_type_rejected(self):
        survey = self._make_survey([
            {"fields": [{"type": "text"}]}
        ])
        for bad in (1, None, []):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    self._response(survey, [[bad]]).validate()

    def test_optional_text_empty_string_accepted(self):
        survey = self._make_survey([
            {"fields": [{"type": "text"}]}
        ])
        self._response(survey, [[""]]).validate()  # Should not raise

    def test_text_long_string_accepted(self):
        survey = self._make_survey([
            {"fields": [{"type": "text"}]}
        ])
        self._response(survey, [["x" * 10_000]]).validate()  # Should not raise

    # --- textarea ---

    def test_textarea_valid_answer_passes(self):
        survey = self._make_survey([
            {"fields": [{"type": "textarea"}]}
        ])
        self._response(survey, [["multi\nline\nvalue"]]).validate()  # Should not raise

    def test_required_textarea_empty_string_rejected(self):
        survey = self._make_survey([
            {"fields": [{"type": "textarea", "required": True}]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [[""]]).validate()

    def test_textarea_wrong_json_type_rejected(self):
        survey = self._make_survey([
            {"fields": [{"type": "textarea"}]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [[42]]).validate()

    # --- likert ---

    def test_likert_valid_answer_passes(self):
        survey = self._make_survey([
            {"fields": [{
                "type": "likert",
                "sublabels": ["Q1", "Q2"],
                "options": ["0", "1", "2"],
            }]}
        ])
        self._response(survey, [[["0", "2"]]]).validate()  # Should not raise

    def test_likert_wrong_json_type_rejected(self):
        survey = self._make_survey([
            {"fields": [{
                "type": "likert",
                "sublabels": ["Q1", "Q2"],
                "options": ["0", "1", "2"],
            }]}
        ])
        for bad in ("0", None, {"0": "1"}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    self._response(survey, [[bad]]).validate()

    def test_likert_non_string_item_rejected(self):
        survey = self._make_survey([
            {"fields": [{
                "type": "likert",
                "sublabels": ["Q1", "Q2"],
                "options": ["0", "1", "2"],
            }]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [[[0, 1]]]).validate()

    def test_likert_too_many_items_rejected(self):
        survey = self._make_survey([
            {"fields": [{
                "type": "likert",
                "sublabels": ["Q1", "Q2"],
                "options": ["0", "1", "2"],
            }]}
        ])
        with self.assertRaises(ValidationError):
            self._response(survey, [[["0", "1", "2"]]]).validate()

    def test_likert_empty_sublabels_accepts_empty_array(self):
        survey = self._make_survey([
            {"fields": [{
                "type": "likert",
                "sublabels": [],
                "options": ["0", "1"],
            }]}
        ])
        self._response(survey, [[[]]]).validate()  # Should not raise

    # --- unknown / fallback type ---

    def test_unknown_type_accepts_any_value(self):
        survey = self._make_survey([
            {"fields": [{"type": "mystery_widget"}]}
        ])
        for value in ("string", 42, None, ["x"], {"k": "v"}):
            with self.subTest(value=value):
                self._response(survey, [[value]]).validate()  # Should not raise

    # --- cross-cutting structural ---

    def test_mixed_type_section_valid_answer(self):
        survey = self._make_survey([{
            "fields": [
                {"type": "text"},
                {"type": "textarea"},
                {"type": "radio", "options": ["Y", "N"]},
                {"type": "select", "options": ["A", "B"]},
                {"type": "checkbox", "options": ["X", "Z"]},
                {"type": "likert", "sublabels": ["R1", "R2"], "options": ["0", "1"]},
            ],
        }])
        self._response(
            survey,
            [["hello", "multi\nline", "Y", "A", ["X"], ["0", "1"]]],
        ).validate()  # Should not raise

    def test_validate_reraises_as_django_validation_error(self):
        survey = self._make_survey([
            {"fields": [{"type": "radio", "options": ["Yes", "No"]}]}
        ])
        response = self._response(survey, [["Maybe"]])
        # Must be Django's ValidationError (not jsonschema's) — the management
        # command and model .clean() callers rely on this contract.
        with self.assertRaises(ValidationError):
            response.validate()
        with self.assertRaises(jsonschema.ValidationError):
            # Sanity check: the underlying jsonschema call would raise its own
            # error class; .validate() must convert it.
            jsonschema.validate(response.answers, survey.response_schema)

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
