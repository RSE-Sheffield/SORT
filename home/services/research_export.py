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

import xlsxwriter
from django.core.exceptions import ValidationError
from django.utils import timezone

from survey.models import Survey, SurveyResponse

SHEET_NAME = "Research data"
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


@dataclass
class ExportDiagnosis:
    """
    Why the export's cells are blank, to tell malformed response data apart from
    the column layout. Every blank answer cell is counted under exactly one cause.
    See https://github.com/RSE-Sheffield/SORT/issues/799
    """

    row_count: int = 0
    column_count: int = 0
    # Blank because the column is a question label from another survey's config
    blank_other_survey: int = 0
    # Blank because the stored answers JSON is shorter than the survey config (malformed data)
    blank_not_stored: int = 0
    # Blank because the answer was stored empty (e.g. an optional field left unanswered)
    blank_empty: int = 0
    # Answers lost because a later field in the same survey has the same label
    overwritten_answers: int = 0
    # Survey ID -> number of consented responses
    rows_per_survey: Counter = field(default_factory=Counter)
    # Survey ID -> number of responses with answers missing from the stored JSON
    short_responses: Counter = field(default_factory=Counter)
    # Survey ID -> [(response ID, validation messages)] for responses failing the JSON Schema
    invalid_responses: dict = field(default_factory=lambda: defaultdict(list))
    # Survey ID -> {label: number of fields with that label}, for labels used more than once
    duplicate_labels: dict = field(default_factory=dict)

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


class ResearchExport:
    """
    Consented research responses flattened to one row each, with the union of
    all surveys' questions as columns.
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

    def _questions(self) -> tuple[dict[int, tuple[str]], list[str]]:
        """
        Each survey's question labels, and the union of them as columns (in survey order,
        matching the order responses are written in).
        """
        questions: dict[str, None] = {}
        fields_cache: dict[int, tuple[str]] = {}
        # Only surveys with a consented response contribute columns, so find them first
        survey_ids = {response.survey_id for response in self.consented_responses()}
        for survey in Survey.objects.filter(pk__in=survey_ids).order_by("pk"):
            fields_cache[survey.pk] = survey.fields
            questions.update(dict.fromkeys(fields_cache[survey.pk]))
        return fields_cache, list(questions)

    def diagnose(self) -> ExportDiagnosis:
        """
        Attribute every blank answer cell of the export to its cause, and check each
        consented response against its survey's JSON Schema. Reads only; writes nothing.
        """
        fields_cache, questions = self._questions()
        diagnosis = ExportDiagnosis(column_count=len(questions))
        for survey_id, labels in fields_cache.items():
            duplicates = {label: count for label, count in Counter(labels).items() if count > 1}
            if duplicates:
                diagnosis.duplicate_labels[survey_id] = duplicates

        for response in self.consented_responses():
            survey_id = response.survey_id
            diagnosis.row_count += 1
            diagnosis.rows_per_survey[survey_id] += 1
            try:
                response.validate()
            except ValidationError as exc:
                diagnosis.invalid_responses[survey_id].append((response.pk, exc.messages))

            labels = fields_cache.get(survey_id) or response.survey.fields
            # Match answers to labels as write_xlsx does: for duplicate labels, the last wins
            cells: dict[str, tuple] = {}
            for label, value, is_stored in zip(labels, response.answers_values, response.answers_stored):
                if label in cells and cells[label][0] not in (None, ""):
                    diagnosis.overwritten_answers += 1
                cells[label] = (value, is_stored)
            if not all(response.answers_stored):
                diagnosis.short_responses[survey_id] += 1

            for question in questions:
                if question not in cells:
                    diagnosis.blank_other_survey += 1
                    continue
                value, is_stored = cells[question]
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
        fields_cache, questions = self._questions()

        workbook = xlsxwriter.Workbook(file, {"constant_memory": True})
        bold = workbook.add_format({"bold": True})
        datetime_format = workbook.add_format({"num_format": DATETIME_FORMAT})
        sheet = workbook.add_worksheet(SHEET_NAME)

        for col_index, heading in enumerate((*METADATA_COLUMNS, *questions)):
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
            # TODO: answers are keyed by question label, so duplicate labels (e.g. two
            # "Other (please specify)" fields, or likert sublabels) collide: dict(zip(...))
            # keeps only the last answer and the header dedup leaves one column. Key by
            # field id instead. See https://github.com/RSE-Sheffield/SORT/pull/748#discussion_r4325196098
            if survey.pk not in fields_cache:
                # First consented response arrived after the header was written; its
                # survey's new questions (if any) have no column and are left out
                fields_cache[survey.pk] = survey.fields
            answers = dict(zip(fields_cache[survey.pk], response.answers_values))
            for offset, question in enumerate(questions):
                _write_cell(sheet, row_index, len(METADATA_COLUMNS) + offset, answers.get(question, ""))
            row_count = row_index
        workbook.close()
        return row_count
