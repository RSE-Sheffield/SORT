"""
Unit tests for survey.misc module
"""

from django.test import TestCase

from survey.misc import test_survey_config


class TestSurveyConfigTestCase(TestCase):
    """Tests for the test_survey_config fixture"""

    def test_test_survey_config_structure(self):
        """Test that test_survey_config has the expected structure"""
        self.assertIsInstance(test_survey_config, dict)
        self.assertIn("sections", test_survey_config)
        self.assertIsInstance(test_survey_config["sections"], list)

    def test_test_survey_config_has_sections(self):
        """Test that test_survey_config has multiple sections"""
        sections = test_survey_config["sections"]
        self.assertGreater(len(sections), 0)
        # Should have at least consent section
        self.assertGreaterEqual(len(sections), 1)

    def test_consent_section(self):
        """Test the consent section structure"""
        sections = test_survey_config["sections"]
        consent_section = sections[0]

        self.assertEqual(consent_section["title"], "Welcome")
        self.assertEqual(consent_section["type"], "consent")
        self.assertIn("fields", consent_section)
        self.assertIsInstance(consent_section["fields"], list)
        self.assertGreater(len(consent_section["fields"]), 0)

    def test_consent_field(self):
        """Test the consent field structure"""
        sections = test_survey_config["sections"]
        consent_section = sections[0]
        consent_field = consent_section["fields"][0]

        self.assertEqual(consent_field["type"], "radio")
        self.assertEqual(consent_field["name"], "consent")
        self.assertEqual(consent_field["label"], "Your agreement to complete the survey")
        self.assertTrue(consent_field["required"])
        self.assertIn("options", consent_field)
        self.assertEqual(len(consent_field["options"]), 2)

    def test_consent_options(self):
        """Test consent field options"""
        sections = test_survey_config["sections"]
        consent_section = sections[0]
        consent_field = consent_section["fields"][0]
        options = consent_field["options"]

        # Check Yes option
        self.assertEqual(options[0][0], "Yes")
        self.assertEqual(options[0][1], "I agree to complete the survey")

        # Check No option
        self.assertEqual(options[1][0], "No")
        self.assertEqual(options[1][1], "I do not agree")

    def test_regular_sections(self):
        """Test regular survey sections structure"""
        sections = test_survey_config["sections"]

        # Should have at least 2 regular sections after consent
        regular_sections = sections[1:]
        self.assertGreaterEqual(len(regular_sections), 2)

        for section in regular_sections[:2]:
            self.assertIn("title", section)
            self.assertIn("description", section)
            self.assertIn("fields", section)
            self.assertIsInstance(section["fields"], list)

    def test_field_types(self):
        """Test that sections contain various field types"""
        sections = test_survey_config["sections"]
        regular_section = sections[1]  # First regular section
        fields = regular_section["fields"]

        field_types = [field["type"] for field in fields]

        # Should contain char, text, checkbox, and radio fields
        self.assertIn("char", field_types)
        self.assertIn("text", field_types)
        self.assertIn("checkbox", field_types)
        self.assertIn("radio", field_types)

    def test_char_field(self):
        """Test char field structure"""
        sections = test_survey_config["sections"]
        regular_section = sections[1]
        char_field = next(f for f in regular_section["fields"] if f["type"] == "char")

        self.assertEqual(char_field["name"], "char_field")
        self.assertEqual(char_field["label"], "Char field")

    def test_text_field(self):
        """Test text field structure"""
        sections = test_survey_config["sections"]
        regular_section = sections[1]
        text_field = next(f for f in regular_section["fields"] if f["type"] == "text")

        self.assertEqual(text_field["name"], "text_field")
        self.assertEqual(text_field["label"], "Text field")

    def test_checkbox_field(self):
        """Test checkbox field structure"""
        sections = test_survey_config["sections"]
        regular_section = sections[1]
        checkbox_field = next(
            f for f in regular_section["fields"] if f["type"] == "checkbox"
        )

        self.assertEqual(checkbox_field["name"], "checkbox_field")
        self.assertEqual(checkbox_field["label"], "Checkbox field")
        self.assertIn("options", checkbox_field)
        self.assertEqual(len(checkbox_field["options"]), 2)

    def test_radio_field(self):
        """Test radio field structure"""
        sections = test_survey_config["sections"]
        regular_section = sections[1]
        radio_field = next(f for f in regular_section["fields"] if f["type"] == "radio")

        self.assertEqual(radio_field["name"], "radio_field")
        self.assertEqual(radio_field["label"], "Radio field")
        self.assertIn("options", radio_field)
        self.assertEqual(len(radio_field["options"]), 2)

    def test_field_options_structure(self):
        """Test that field options have correct structure"""
        sections = test_survey_config["sections"]
        regular_section = sections[1]

        for field in regular_section["fields"]:
            if "options" in field:
                options = field["options"]
                self.assertIsInstance(options, list)
                for option in options:
                    self.assertIsInstance(option, list)
                    self.assertEqual(len(option), 2)  # [value, label]
                    self.assertIsInstance(option[0], str)
                    self.assertIsInstance(option[1], str)

    def test_multiple_sections_same_structure(self):
        """Test that multiple sections can have similar structures"""
        sections = test_survey_config["sections"]

        # Get regular sections (excluding consent)
        regular_sections = [s for s in sections if s.get("type") != "consent"]

        if len(regular_sections) >= 2:
            section1 = regular_sections[0]
            section2 = regular_sections[1]

            # Both should have fields
            self.assertIn("fields", section1)
            self.assertIn("fields", section2)

            # Both should have same number of fields in this test config
            self.assertEqual(len(section1["fields"]), len(section2["fields"]))
