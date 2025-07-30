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

    def test_csv_export(self):
        """
        The survey CSV export function should export the survey CSV file.
        """
        # Generate CSV data
        buffer = io.StringIO()
        buffer.write(self.survey.to_csv())
        buffer.seek(0)

        # Validate CSV
        for _ in csv.reader(buffer):
            pass
