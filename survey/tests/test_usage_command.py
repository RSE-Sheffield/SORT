"""
Test the `usage` management command (issue #726).
"""

import csv
import io
import json

from django.core.management import call_command
from django.core.management.base import CommandError

import SORT.test.test_case
from SORT.test.model_factory import SurveyFactory
from survey.models import SurveyResponse


class UsageCommandTestCase(SORT.test.test_case.ServiceTestCase):

    def setUp(self):
        super().setUp()
        self.survey = SurveyFactory()
        SurveyResponse.objects.create(survey=self.survey, answers=[])

    def _call(self, *args):
        stdout = io.StringIO()
        call_command("usage", *args, stdout=stdout, stderr=io.StringIO())
        return stdout.getvalue()

    def test_default_is_legacy_csv(self):
        rows = list(csv.reader(io.StringIO(self._call())))
        self.assertEqual(
            rows[0], ["Organisation", "Project", "Survey ID", "Survey", "Survey created at", "Responses"]
        )
        self.assertEqual(rows[1][2], str(self.survey.pk))
        self.assertEqual(rows[1][5], "1")

    def test_text(self):
        output = self._call("--format", "text")
        self.assertIn("SORT Online usage report", output)
        self.assertIn(self.survey.organisation.name, output)

    def test_json(self):
        data = json.loads(self._call("--format", "json"))
        self.assertEqual(data["summary"]["responses"]["total"], 1)
        self.assertEqual(data["active_days"], 90)

    def test_csv_surveys(self):
        rows = list(csv.DictReader(io.StringIO(self._call("--format", "csv"))))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["survey_id"], str(self.survey.pk))
        self.assertEqual(rows[0]["responses"], "1")

    def test_csv_trends(self):
        rows = list(csv.DictReader(io.StringIO(self._call("--format", "csv", "--report", "trends"))))
        self.assertEqual(rows[-1]["responses_total"], "1")

    def test_active_days(self):
        data = json.loads(self._call("--format", "json", "--active-days", "7"))
        self.assertEqual(data["active_days"], 7)

    def test_invalid_active_days(self):
        with self.assertRaises(CommandError):
            self._call("--format", "text", "--active-days", "0")

    def test_active_days_too_large(self):
        with self.assertRaises(CommandError):
            self._call("--format", "text", "--active-days", "1000000")
