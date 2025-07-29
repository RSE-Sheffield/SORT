import csv
import tempfile

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

        survey = SurveyFactory()
        survey.initialise()
        survey.generate_mock_responses()

        with tempfile.TemporaryFile(mode="w") as file:
            file.write(survey.to_csv())

            file.seek(0)

            # Validate CSV
            reader = csv.reader(file)
            for row in reader:
                pass
