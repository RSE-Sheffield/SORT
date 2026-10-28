"""
Bulk research data export service.

Collects every survey response that may be used for research, across all
organisations, into a single Excel worksheet. A response is consented research
data only when both:

* its survey has a data sharing agreement (`Survey.is_shared`), and
* the participant ticked the research consent box (`SurveyResponse.has_research_consent`).

This is a platform-wide export rather than a user-scoped operation, so methods
are not gated with `@requires_permission`. Access is enforced by the callers:
the staff console (`StaffRequiredMixin`) and the `research_export` management
command (server shell access).
"""

from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import IO

import jsonschema
import xlsxwriter
from django.core.exceptions import ValidationError
from django.utils import timezone

from survey.models import Survey, SurveyResponse

SHEET_NAME = "Research data"
# Maps each question column to the wording(s) participants saw
QUESTIONS_SHEET_NAME = "Questions"
QUESTIONS_COLUMNS = ("Column", "Question", "Survey IDs")
# Columns that identify where each response came from, before the survey questions
METADATA_COLUMNS = (
    "Organisation",
    "Project",
    "Survey ID",
    "Survey",
    "Response ID",
    "Submitted at",
)
# Excel date-time display format for the "Submitted at" column
DATETIME_FORMAT = "yyyy-mm-dd hh:mm:ss"
# Invalid responses kept as examples per survey by `diagnose`, so memory doesn't grow with the export
EXAMPLES_PER_SURVEY = 3
# Validation messages can quote the participant's whole answers JSON, so cut them short
MAX_MESSAGE_LENGTH = 200


@dataclass
class ExportDiagnosis:
    """
    Why the export's cells are blank, to tell malformed response data apart from
    the column layout. Every blank answer cell is counted under exactly one cause.
    See https://github.com/RSE-Sheffield/SORT/issues/799
    """

    row_count: int = 0
    column_count: int = 0
    # Blank because the column is a question that this response's survey doesn't have
    blank_other_survey: int = 0
    # Blank because the stored answers JSON is shorter than the survey config (malformed data)
    blank_not_stored: int = 0
    # Blank because the answer was stored empty (e.g. an optional field left unanswered)
    blank_empty: int = 0
    # Survey ID -> number of consented responses
    rows_per_survey: Counter = field(default_factory=Counter)
    # Survey ID -> number of responses with answers missing from the stored JSON
    short_responses: Counter = field(default_factory=Counter)
    # Survey ID -> number of responses failing the JSON Schema
    invalid_responses: Counter = field(default_factory=Counter)
    # Survey ID -> [(response ID, truncated validation messages)] for the first few invalid responses
    invalid_examples: dict = field(default_factory=lambda: defaultdict(list))
    # Survey ID -> {question ID: number of fields with that ID}, for IDs used more than once.
    # These fields are exported as separate, numbered columns (see Survey.field_ids)
    repeated_ids: dict = field(default_factory=dict)

    @property
    def blank_count(self) -> int:
        return self.blank_other_survey + self.blank_not_stored + self.blank_empty


def _write_cell(sheet, row: int, col: int, value) -> None:
    """
    Write a value, always storing text as a literal string. Participants'
    free-text answers must never be interpreted as Excel formulas (formula injection).
    """
    if value is None or value == "":
        return  # Leave the cell empty
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        sheet.write_number(row, col, value)
    else:
        sheet.write_string(row, col, str(value))


@dataclass
class ExportColumns:
    """
    The export's question columns, gathered from each survey with consented responses.
    """

    # Survey ID -> that survey's question IDs (Survey.field_ids)
    ids_cache: dict[int, tuple[str]] = field(default_factory=dict)
    # Union of all surveys' question IDs, in survey order (a dict keeps insertion order)
    columns: dict[str, None] = field(default_factory=dict)
    # Question ID -> {wording: [survey IDs]}
    wordings: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(list)))
    # Survey ID -> {question ID: count}, for IDs used more than once in that survey
    repeated_ids: dict[int, dict[str, int]] = field(default_factory=dict)

    def add_survey(self, survey: Survey, add_columns: bool = False) -> None:
        """
        Record a survey's question IDs and wordings.

        :param add_columns: Add the survey's new question IDs as columns. Once the header is
            written, columns are fixed, so the wordings of questions without a column are left out.
        """
        field_ids = survey.field_ids
        self.ids_cache[survey.pk] = field_ids
        if add_columns:
            self.columns.update(dict.fromkeys(field_ids))
        for field_id, label in zip(field_ids, survey.fields):
            if field_id in self.columns:
                self.wordings[field_id][label].append(survey.pk)
        repeated = {field_id: count for field_id, count in Counter(survey.field_ids_iter()).items() if count > 1}
        if repeated:
            self.repeated_ids[survey.pk] = repeated


class ResearchExport:
    """
    Consented research responses flattened to one row each, with the union of
    all surveys' questions as columns. Columns are keyed by stable question
    identifiers (Survey.field_ids) rather than labels, so the same question worded
    differently in different surveys (e.g. profession variants) shares one column.
    """

    def consented_responses(self) -> Iterator[SurveyResponse]:
        """
        Responses on shared surveys whose participant gave research consent.

        Surveys that were never initialised have no consent question, so they are skipped.
        """
        responses = (
            SurveyResponse.objects.filter(survey__is_shared=True, survey__survey_config__isnull=False)
            .select_related("survey__project__organisation")
            .order_by("survey_id", "pk")
        )
        # Participant consent lives inside the answers JSON, so filter in Python
        return (response for response in responses.iterator() if response.has_research_consent)

    def _columns(self) -> ExportColumns:
        """
        Each survey's question identifiers, the union of them as columns (in survey order,
        matching the order responses are written in), and the wordings of each column's
        question with the surveys that used them.
        """
        export_columns = ExportColumns()
        # Only surveys with a consented response contribute columns, so find them first
        survey_ids = {response.survey_id for response in self.consented_responses()}
        for survey in Survey.objects.filter(pk__in=survey_ids).order_by("pk"):
            export_columns.add_survey(survey, add_columns=True)
        return export_columns

    def diagnose(self, max_examples: int | None = EXAMPLES_PER_SURVEY) -> ExportDiagnosis:
        """
        Attribute every blank answer cell of the export to its cause, and check each
        consented response against its survey's JSON Schema. Reads only; writes nothing.

        :param max_examples: Invalid responses to keep as examples per survey (None keeps all)
        """
        export_columns = self._columns()
        ids_cache, columns = export_columns.ids_cache, export_columns.columns
        # Each response has its own Survey instance, so build each survey's validator once here
        validators: dict[int, jsonschema.protocols.Validator] = {}
        diagnosis = ExportDiagnosis(column_count=len(columns), repeated_ids=export_columns.repeated_ids)

        for response in self.consented_responses():
            survey_id = response.survey_id
            diagnosis.row_count += 1
            diagnosis.rows_per_survey[survey_id] += 1
            if survey_id not in validators:
                validators[survey_id] = response.survey.response_validator
            try:
                response.validate(validators[survey_id])
            except ValidationError as exc:
                diagnosis.invalid_responses[survey_id] += 1
                examples = diagnosis.invalid_examples[survey_id]
                if max_examples is None or len(examples) < max_examples:
                    messages = [
                        message[:MAX_MESSAGE_LENGTH] + "..." if len(message) > MAX_MESSAGE_LENGTH else message
                        for message in exc.messages
                    ]
                    examples.append((response.pk, messages))

            if survey_id not in ids_cache:
                # As in write_xlsx: a survey first seen after the columns were chosen
                # has no columns for its new questions, so those answers are left out
                export_columns.add_survey(response.survey)
            cells = dict(zip(ids_cache[survey_id], response.answers_with_stored))
            if not all(is_stored for _, is_stored in cells.values()):
                diagnosis.short_responses[survey_id] += 1

            for column in columns:
                if column not in cells:
                    diagnosis.blank_other_survey += 1
                    continue
                value, is_stored = cells[column]
                if value not in (None, ""):
                    continue
                if is_stored:
                    diagnosis.blank_empty += 1
                else:
                    diagnosis.blank_not_stored += 1
        return diagnosis

    def write_xlsx(self, file: IO[bytes] | str) -> int:
        """
        Write the export as an Excel workbook. Rows are streamed from the database to
        disk-backed temporary files one at a time, so memory use doesn't grow with the export.

        :param file: A file path or binary file-like object
        :returns: The number of responses written
        """
        # The header needs every column up front, before any row is written
        export_columns = self._columns()
        ids_cache, columns = export_columns.ids_cache, export_columns.columns

        workbook = xlsxwriter.Workbook(file, {"constant_memory": True})
        bold = workbook.add_format({"bold": True})
        datetime_format = workbook.add_format({"num_format": DATETIME_FORMAT})
        sheet = workbook.add_worksheet(SHEET_NAME)

        for col_index, heading in enumerate((*METADATA_COLUMNS, *columns)):
            sheet.write_string(0, col_index, heading, bold)
        sheet.freeze_panes(1, 0)
        submitted_col = METADATA_COLUMNS.index("Submitted at")
        row_count = 0
        for row_index, response in enumerate(self.consented_responses(), start=1):
            survey: Survey = response.survey
            project = survey.project  # Shared surveys need not belong to a project
            metadata = (
                project.organisation.name if project else "",
                project.name if project else "",
                survey.pk,
                survey.name,
                response.pk,
            )
            for col_index, value in enumerate(metadata):
                _write_cell(sheet, row_index, col_index, value)
            sheet.write_datetime(row_index, submitted_col, timezone.make_naive(response.created_at), datetime_format)
            if survey.pk not in ids_cache:
                # First consented response arrived after the header was written; its
                # survey's new questions (if any) have no column and are left out
                export_columns.add_survey(survey)
            answers = dict(zip(ids_cache[survey.pk], response.answers_values))
            for offset, column in enumerate(columns):
                _write_cell(sheet, row_index, len(METADATA_COLUMNS) + offset, answers.get(column, ""))
            row_count = row_index

        self._write_questions_sheet(workbook.add_worksheet(QUESTIONS_SHEET_NAME), bold, export_columns.wordings)
        workbook.close()
        return row_count

    @staticmethod
    def _write_questions_sheet(sheet, bold, wordings: dict[str, dict[str, list[int]]]) -> None:
        """
        List the wording of each column's question, one row per distinct wording, with the
        surveys that used it, so researchers can see the exact text each participant saw.
        """
        for col_index, heading in enumerate(QUESTIONS_COLUMNS):
            sheet.write_string(0, col_index, heading, bold)
        sheet.freeze_panes(1, 0)
        rows = (
            (column, label, survey_ids) for column, labels in wordings.items() for label, survey_ids in labels.items()
        )
        for row_index, (column, label, survey_ids) in enumerate(rows, start=1):
            _write_cell(sheet, row_index, 0, column)
            _write_cell(sheet, row_index, 1, label)
            _write_cell(sheet, row_index, 2, ", ".join(map(str, survey_ids)))
