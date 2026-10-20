import csv
import io

from django.test import TestCase

from SORT.test.model_factory import SurveyFactory
from survey.models import SurveyResponse


class TestSurveyCsvExport(TestCase):
    """
    Test the CSV data export functionality.
    """

    def setUp(self):
        self.survey = SurveyFactory()
        self.survey.initialise()
        self.survey.generate_mock_responses()

    def test_csv_export_with_multiple_checkbox_selections(self):
        """
        A checkbox field with more than one selected option should collapse into a
        single CSV column instead of overflowing into extra, unnamed columns.

        Regression test for https://github.com/UniversityOfSheffield/SORT/issues/705
        """
        survey = SurveyFactory()
        survey.survey_config = {
            "sections": [
                {
                    "title": "Section 1",
                    "fields": [
                        {
                            "type": "checkbox",
                            "name": "colours",
                            "label": "Which colours do you like?",
                            "sublabels": [],
                            "options": ["Red", "Green", "Blue"],
                        }
                    ],
                }
            ]
        }
        survey.save()
        survey.accept_response([[["Red", "Blue"]]])

        csv_data = survey.to_csv()

        csv_file = io.StringIO(csv_data)
        rows = list(csv.DictReader(csv_file))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Which colours do you like?"], "Red, Blue")

    def test_csv_export_with_a_checkbox_answer_stored_as_a_string(self):
        """
        A checkbox answer should be one column even when the stored value is a bare
        string rather than a list of selected options, which is the shape of some
        answers recorded before response validation existed.
        """
        survey = SurveyFactory()
        survey.survey_config = {
            "sections": [
                {
                    "title": "Section 1",
                    "fields": [
                        {
                            "type": "checkbox",
                            "name": "colours",
                            "label": "Which colours do you like?",
                            "sublabels": [],
                            "options": ["Red", "Green", "Blue"],
                        }
                    ],
                }
            ]
        }
        survey.save()
        # Bypass validation: this shape can no longer be submitted, but it exists
        SurveyResponse.objects.create(survey=survey, answers=[["Red"]])

        rows = list(csv.DictReader(io.StringIO(survey.to_csv())))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Which colours do you like?"], "Red")

    def test_csv_export_with_answers_missing_from_a_response(self):
        """
        A response holding fewer answers than the survey has questions should still
        produce one cell per column, so the remaining answers stay under the right
        headings.
        """
        answers = self.survey._generate_mock_response()
        # Drop the last field of the first section, and the whole final section
        del answers[0][-1]
        del answers[-1]
        SurveyResponse.objects.create(survey=self.survey, answers=answers)

        rows = list(csv.DictReader(io.StringIO(self.survey.to_csv())))

        self.assertEqual(len(rows), self.survey.responses_count)
        for row in rows:
            self.assertEqual(len(row), len(self.survey.fields))
            self.assertNotIn(None, row.keys(), "Answers overflowed past the headings")

    def test_csv_export(self):
        """
        The survey CSV export function should export valid CSV data.
        """

        # Generate CSV data as a string
        csv_data = self.survey.to_csv()
        # Check the data isn't empty with just newlines
        self.assertTrue(csv_data.strip(), "CSV data empty")

        # Parse CSV data
        csv_file = io.StringIO(csv_data)
        rows = list(csv.DictReader(csv_file))

        # Check row count
        self.assertGreater(len(rows), 0, "CSV should contain at least one row")
        self.assertEqual(
            len(rows), self.survey.responses_count, "Unexpected number of CSV data rows"
        )

        # Check there's some responses
        for row in rows:
            self.assertGreater(len(row), 0, "No fields in response")
            for question, answer in row.items():
                self.assertIsNotNone(
                    question,
                )
                self.assertTrue(question)
                self.assertIsNotNone(answer, f"missing answer for {question}")
                self.assertTrue(answer, f"question: {question} answer: {answer}")
