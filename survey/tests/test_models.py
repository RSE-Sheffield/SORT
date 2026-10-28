import json

from django.conf import settings
from django.db import IntegrityError
from django.test import TestCase

from SORT.test.model_factory import SurveyFactory
from survey.models import Profession, SurveyEvidenceSection


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


class TestSurveyConfigSublabels(TestCase):
    """
    Regression tests for sublabel wording in survey config JSON files.
    Guards against double spaces and incorrect phrasing in E3/E4 sublabels.
    """

    def _get_all_sublabels(self, config: dict) -> list[str]:
        sublabels = []
        for section in config.get("sections", []):
            for field in section.get("fields", []):
                sublabels.extend(field.get("sublabels", []))
        return sublabels

    def _load_config(self, filename: str) -> dict:
        path = settings.SURVEY_TEMPLATE_DIR / filename
        with path.open() as f:
            return json.load(f)

    def test_no_double_spaces_in_e3_e4_sublabels(self):
        """E3 and E4 sublabels must not contain double spaces."""
        for filename in settings.SURVEY_TEMPLATES.values():
            config = self._load_config(filename)
            sublabels = self._get_all_sublabels(config)
            for label_prefix in ("E3.", "E4."):
                text = next((s for s in sublabels if s.startswith(label_prefix)), None)
                if text is None:
                    continue
                self.assertNotIn(
                    "  ",
                    text,
                    msg=f"Double space found in {label_prefix} sublabel in {filename!r}: {text!r}",
                )

    def test_e3_e4_sublabel_phrasing(self):
        """E3 and E4 sublabels must use 'on the use of … to support' phrasing."""
        for filename in settings.SURVEY_TEMPLATES.values():
            config = self._load_config(filename)
            sublabels = self._get_all_sublabels(config)
            e3 = next((s for s in sublabels if s.startswith("E3.")), None)
            e4 = next((s for s in sublabels if s.startswith("E4.")), None)
            for label, text in [("E3", e3), ("E4", e4)]:
                if text is None:
                    continue
                self.assertIn(
                    "on the use of digital technology to support",
                    text,
                    msg=f"{label} sublabel in {filename!r} has unexpected phrasing: {text!r}",
                )


class TestSurveyFieldIds(TestCase):
    """
    Stable question identifiers, used to align questions across surveys whose wording differs.
    See https://github.com/RSE-Sheffield/SORT/issues/799
    """

    def _survey(self, profession: Profession):
        survey = SurveyFactory(survey_body_path=profession)
        survey.initialise()
        return survey

    def test_field_ids_are_unique_and_aligned_with_fields(self):
        for profession in Profession:
            survey = self._survey(profession)
            with self.subTest(profession=profession):
                self.assertEqual(len(survey.field_ids), len(survey.fields))
                self.assertEqual(len(set(survey.field_ids)), len(survey.field_ids))

    def test_sort_question_ids_are_the_same_in_every_profession_variant(self):
        def sort_ids(survey):
            # Drop the consent (first) and demography (last) sections
            consent = len(survey.sections[0]["fields"])
            demography = len(survey.sections[-1]["fields"])
            return survey.field_ids[consent:-demography]

        expected = sort_ids(self._survey(Profession.NURSES))
        self.assertEqual(expected[:3], ("A1", "A2", "A3"))
        self.assertIn("releasing_potential_comments", expected)
        for profession in Profession:
            with self.subTest(profession=profession):
                self.assertEqual(sort_ids(self._survey(profession)), expected)

    def test_repeated_labels_are_numbered(self):
        survey = self._survey(Profession.NURSES)
        survey.survey_config["sections"][-1]["fields"].append({"type": "text", "label": "What is your profession?"})
        self.assertEqual(survey.field_ids[-1], "What is your profession? (2)")
        self.assertEqual(survey.field_ids.count("What is your profession?"), 1)

    def test_custom_likert_sublabels_do_not_take_question_codes(self):
        survey = self._survey(Profession.NURSES)
        sublabels = ["A1. I feel supported", "Q1. My manager is research-active"]
        custom_section = {
            "title": "Custom",
            "type": "custom",
            "fields": [{"type": "likert", "label": "Custom likert", "sublabels": sublabels, "options": ["Yes", "No"]}],
        }
        # After consent, before the SORT sections
        survey.survey_config["sections"].insert(1, custom_section)
        consent = len(survey.sections[0]["fields"])
        self.assertEqual(survey.field_ids[consent : consent + 2], tuple(sublabels))
        self.assertIn("A1", survey.field_ids)
        self.assertNotIn("A1 (2)", survey.field_ids)
