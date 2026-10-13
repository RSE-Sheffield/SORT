"""
Bulk export of consented research data (shared surveys, participants who gave research consent).
"""

import io
import tempfile
from io import StringIO
from pathlib import Path

import openpyxl
from django.core.management import call_command
from django.test import TestCase

from home.services.research_export import METADATA_COLUMNS, SHEET_NAME, ResearchExport
from SORT.test.model_factory import SurveyFactory
from survey.models import RESEARCH_CONSENT_FIELD_NAME, Survey, SurveyResponse

EXTRA_QUESTION = "Extra question"


def field_index(survey: Survey, name: str) -> int:
    fields = survey.sections[0]["fields"]
    return next(i for i, f in enumerate(fields) if f["name"] == name)


def make_survey(is_shared: bool = True, extra_question: bool = False) -> Survey:
    survey = SurveyFactory(is_shared=is_shared)
    survey.initialise()
    if extra_question:
        survey.survey_config["sections"].append(
            {"title": "Extra", "fields": [{"type": "text", "name": "extra", "label": EXTRA_QUESTION}]}
        )
    survey.save()
    return survey


def make_response(survey: Survey, research_consent: bool, extra_answer: str = None) -> SurveyResponse:
    answers = survey._generate_mock_response()
    index = field_index(survey, RESEARCH_CONSENT_FIELD_NAME)
    option = survey.sections[0]["fields"][index]["options"][0]
    answers[0][index] = [option] if research_consent else []
    if extra_answer is not None:
        answers[-1] = [extra_answer]
    return SurveyResponse.objects.create(survey=survey, answers=answers)


def read_sheet(export: ResearchExport) -> list[tuple]:
    buffer = io.BytesIO()
    export.write_xlsx(buffer)
    workbook = openpyxl.load_workbook(io.BytesIO(buffer.getvalue()))
    return list(workbook[SHEET_NAME].iter_rows(values_only=True))


class ResearchExportTestCase(TestCase):
    def test_includes_only_consented_responses_on_shared_surveys(self):
        shared = make_survey(is_shared=True)
        unshared = make_survey(is_shared=False)
        consented = make_response(shared, research_consent=True)
        make_response(shared, research_consent=False)
        make_response(unshared, research_consent=True)

        rows = read_sheet(ResearchExport())
        response_id_col = METADATA_COLUMNS.index("Response ID")
        self.assertEqual([row[response_id_col] for row in rows[1:]], [consented.pk])
        self.assertEqual(ResearchExport().summary(), {"surveys": 1, "responses": 1})

    def test_metadata_columns(self):
        survey = make_survey()
        response = make_response(survey, research_consent=True)

        header, row = read_sheet(ResearchExport())
        self.assertEqual(header[: len(METADATA_COLUMNS)], METADATA_COLUMNS)
        self.assertEqual(
            row[:5],
            (survey.organisation.name, survey.project.name, survey.pk, survey.name, response.pk),
        )
        self.assertIsNotNone(row[5])

    def test_columns_are_union_of_survey_questions(self):
        plain = make_survey()
        extended = make_survey(extra_question=True)
        make_response(plain, research_consent=True)
        make_response(extended, research_consent=True, extra_answer="Hello")

        header, plain_row, extended_row = read_sheet(ResearchExport())
        self.assertEqual(header.count(EXTRA_QUESTION), 1)
        self.assertEqual(header[len(METADATA_COLUMNS):], (*plain.fields, EXTRA_QUESTION))
        extra_col = header.index(EXTRA_QUESTION)
        self.assertIsNone(plain_row[extra_col])
        self.assertEqual(extended_row[extra_col], "Hello")

    def test_answers_are_not_written_as_formulas(self):
        survey = make_survey(extra_question=True)
        make_response(survey, research_consent=True, extra_answer="=1+1")

        header, row = read_sheet(ResearchExport())
        self.assertEqual(row[header.index(EXTRA_QUESTION)], "=1+1")
        buffer = io.BytesIO()
        ResearchExport().write_xlsx(buffer)
        sheet = openpyxl.load_workbook(io.BytesIO(buffer.getvalue()))[SHEET_NAME]
        self.assertEqual(sheet.cell(row=2, column=header.index(EXTRA_QUESTION) + 1).data_type, "s")

    def test_empty_export_has_header_only(self):
        rows = read_sheet(ResearchExport())
        self.assertEqual(rows, [METADATA_COLUMNS])
        self.assertEqual(ResearchExport().summary(), {"surveys": 0, "responses": 0})


class ResearchExportCommandTestCase(TestCase):
    def test_writes_workbook(self):
        survey = make_survey()
        make_response(survey, research_consent=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "research.xlsx"
            out = StringIO()
            call_command("research_export", "-o", str(path), stdout=out)
            self.assertIn("Wrote 1 responses", out.getvalue())
            rows = list(openpyxl.load_workbook(path)[SHEET_NAME].iter_rows(values_only=True))
            self.assertEqual(len(rows), 2)
