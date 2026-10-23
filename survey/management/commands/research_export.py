from django.core.management import BaseCommand, CommandError

from home.services.research_export import ExportDiagnosis, ResearchExport

# Example responses listed per survey, unless --verbosity 2 or more asks for all of them
EXAMPLES_PER_SURVEY = 3
# Validation messages can quote the participant's whole answers JSON, so cut them short
MAX_MESSAGE_LENGTH = 200


class Command(BaseCommand):
    """
    Export all consented research data (shared surveys, participants who gave
    research consent) across every organisation to one Excel workbook.
    """

    help = "Export all consented research data to an Excel (.xlsx) file."

    def add_arguments(self, parser):
        parser.add_argument("-o", "--output", help="Output .xlsx file path")
        parser.add_argument(
            "--diagnose",
            action="store_true",
            help="Report why export cells are blank and which responses are malformed, instead of exporting",
        )

    def handle(self, *args, output=None, diagnose=False, verbosity=1, **options):
        if diagnose:
            self.report(ResearchExport().diagnose(), show_all=verbosity >= 2)
            return
        if not output:
            raise CommandError("Provide an output file with -o/--output, or use --diagnose")
        row_count = ResearchExport().write_xlsx(output)
        self.stdout.write(f"Wrote {row_count} responses to {output}")

    def report(self, diagnosis: ExportDiagnosis, show_all: bool) -> None:
        def share(count: int) -> str:
            return f"{count / diagnosis.blank_count:.1%}" if diagnosis.blank_count else "0.0%"

        limit = None if show_all else EXAMPLES_PER_SURVEY
        write = self.stdout.write
        write(
            f"Rows: {diagnosis.row_count} from {len(diagnosis.rows_per_survey)} surveys  "
            f"Question columns: {diagnosis.column_count}  "
            f"Blank answer cells: {diagnosis.blank_count}"
        )
        causes = (
            ("Question from another survey's config", diagnosis.blank_other_survey),
            ("Missing from stored answers (malformed)", diagnosis.blank_not_stored),
            ("Answered empty (e.g. optional field)", diagnosis.blank_empty),
        )
        for cause, count in causes:
            write(f"  {cause + ':':<41}{count} ({share(count)})")
        write(f"Answers overwritten by duplicate labels: {diagnosis.overwritten_answers}")

        write(f"\nResponses with answers missing from stored JSON: {sum(diagnosis.short_responses.values())}")
        for survey_id, count in sorted(diagnosis.short_responses.items()):
            write(f"  Survey {survey_id}: {count} of {diagnosis.rows_per_survey[survey_id]} responses")

        invalid_count = sum(len(items) for items in diagnosis.invalid_responses.values())
        write(f"\nResponses failing JSON Schema validation: {invalid_count}")
        for survey_id, items in sorted(diagnosis.invalid_responses.items()):
            write(f"  Survey {survey_id}: {len(items)} of {diagnosis.rows_per_survey[survey_id]} responses")
            for response_id, messages in items[:limit]:
                for message in messages:
                    if len(message) > MAX_MESSAGE_LENGTH:
                        message = message[:MAX_MESSAGE_LENGTH] + "..."
                    write(f"    Response {response_id}: {message}")

        write(f"\nSurveys with duplicate question labels: {len(diagnosis.duplicate_labels)}")
        for survey_id, duplicates in sorted(diagnosis.duplicate_labels.items()):
            for label, count in duplicates.items():
                write(f"  Survey {survey_id}: {count} fields labelled {label!r}")
