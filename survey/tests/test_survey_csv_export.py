import csv
import io

from django.test import TestCase

from SORT.test.model_factory import SurveyFactory


class TestSurveyCsvExport(TestCase):
    """
    Test the CSV data export functionality.
    """

    def test_csv_export(self):
        """
        The survey CSV export function should export the survey CSV file.
        """

        num_responses = 10

        survey = SurveyFactory()
        survey.initialise()
        survey.generate_mock_responses(num_responses=num_responses)

        csv_data = survey.to_csv()
        self.assertTrue(csv_data.strip(), "CSV export failed")

        csv_file = io.StringIO(csv_data)
        rows = list(csv.DictReader(csv_file))

        self.assertGreater(len(rows), 0, "CSV should contain at least one row")
        self.assertEqual(len(rows), survey.responses_count, "Unexpected number of CSV data rows")
