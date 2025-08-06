import csv
import io
import tempfile

from django.test import TestCase

from SORT.test.model_factory import SurveyFactory


class TestSurveyCsvExport(TestCase):
    """
    Test the CSV data export functionality.
    """

    def setUp(self):
        # Set up survey data
        self.survey = SurveyFactory()
        self.survey.initialise()
        self.survey.generate_mock_responses()

    def test_survey_response_count(self):
        assert self.survey.responses_count

    def test_survey_fields(self):
        assert self.survey.fields

    def test_survey_responses_iter_values(self):
        for value in self.survey.responses_iter_values():
            value = tuple(value)
            assert value

    def test_survey_responses_iter(self):
        for row in self.survey.responses_iter():
            assert row
            self.assertIsInstance(row, dict)

    def test_csv_export(self):
        """
        The survey CSV export function should export the survey CSV file.
        """
        csv_data = self.survey.to_csv()

        if not csv_data.strip():
            raise ValueError("No CSV data generated")

        rows = tuple(csv.reader(csv_data))

        # Check response count
        self.assertEqual(self.survey.responses_count, len(rows))
