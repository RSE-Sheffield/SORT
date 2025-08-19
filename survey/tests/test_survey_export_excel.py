import io

from django.test import TestCase

from SORT.test.model_factory import SurveyFactory


class TestSurveyExport(TestCase):
    """
    Test the data export functionality.
    """

    def setUp(self):
        # Set up survey data
        self.survey = SurveyFactory()
        self.survey.initialise()
        self.survey.generate_mock_responses()

    def test_excel_export(self):
        """
        The survey Excel export function should export a workbook containing survey responses.
        """
        # Generate CSV data
        buffer = io.BytesIO()
        buffer.write(self.survey.to_excel())
        buffer.seek(0)
