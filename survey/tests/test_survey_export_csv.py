import csv
import io

from django.test import TestCase

from SORT.test.model_factory import SurveyFactory


class TestSurveyCsvExport(TestCase):
    """
    Test the CSV data export functionality.
    """

    def setUp(self):
        self.survey = SurveyFactory()
        self.survey.initialise()
        self.survey.generate_mock_responses()

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
