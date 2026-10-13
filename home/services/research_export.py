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

from typing import IO, Iterator

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
        """
        responses = (
            SurveyResponse.objects.filter(survey__is_shared=True)
            .select_related("survey__project__organisation")
            .order_by("survey_id", "pk")
        )
        # Participant consent lives inside the answers JSON, so filter in Python
        return (response for response in responses.iterator() if response.has_research_consent)

    def summary(self) -> dict[str, int]:
        """
        How many surveys and responses the export would contain.
        """
        survey_ids = set()
        responses = 0
        for response in self.consented_responses():
            survey_ids.add(response.survey_id)
            responses += 1
        return {"surveys": len(survey_ids), "responses": responses}

    def _rows(self) -> tuple[list[str], list[dict]]:
        """
        Build the question columns (in order of first appearance) and one dict per response.
        """
        questions: dict[str, None] = {}
        rows = []
        fields_cache: dict[int, tuple[str]] = {}
        for response in self.consented_responses():
            survey: Survey = response.survey
            if survey.pk not in fields_cache:
                fields_cache[survey.pk] = survey.fields
                questions.update(dict.fromkeys(fields_cache[survey.pk]))
            row = {
                "Organisation": survey.project.organisation.name,
                "Project": survey.project.name,
                "Survey ID": survey.pk,
                "Survey": survey.name,
                "Response ID": response.pk,
                "Submitted at": timezone.make_naive(response.created_at),
            }
            row["answers"] = dict(zip(fields_cache[survey.pk], response.answers_values))
            rows.append(row)
        return list(questions), rows

    def write_xlsx(self, file: IO[bytes] | str) -> int:
        """
        Write the export as an Excel workbook.

        :param file: A file path or binary file-like object
        :returns: The number of responses written
        """
        questions, rows = self._rows()
        workbook = xlsxwriter.Workbook(file, {"in_memory": True})
        bold = workbook.add_format({"bold": True})
        datetime_format = workbook.add_format({"num_format": DATETIME_FORMAT})
        sheet = workbook.add_worksheet(SHEET_NAME)

        for col_index, heading in enumerate((*METADATA_COLUMNS, *questions)):
            sheet.write_string(0, col_index, heading, bold)
        sheet.freeze_panes(1, 0)
        submitted_col = METADATA_COLUMNS.index("Submitted at")
        for row_index, row in enumerate(rows, start=1):
            for col_index, column in enumerate(METADATA_COLUMNS):
                if col_index == submitted_col:
                    sheet.write_datetime(row_index, col_index, row[column], datetime_format)
                else:
                    _write_cell(sheet, row_index, col_index, row[column])
            answers = row["answers"]
            for offset, question in enumerate(questions):
                _write_cell(sheet, row_index, len(METADATA_COLUMNS) + offset, answers.get(question, ""))
        workbook.close()
        return len(rows)
