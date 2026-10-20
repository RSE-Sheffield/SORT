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

from collections.abc import Iterator
from typing import IO

import xlsxwriter
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
