from django.core.management import BaseCommand, CommandError

from home.services.research_export import EXAMPLES_PER_SURVEY, ExportDiagnosis, ResearchExport


class Command(BaseCommand):
    """
    Export all consented research data (shared surveys, participants who gave
    research consent) across every organisation to one Excel workbook.
    """

    help = "Export all consented research data to an Excel (.xlsx) file."

    def add_arguments(self, parser):
        # --diagnose writes no workbook, so an output path would be silently ignored
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-o", "--output", help="Output .xlsx file path")
        group.add_argument(
            "--diagnose",
            action="store_true",
            help="Report why export cells are blank and which responses are malformed, instead of exporting",
        )

    def handle(self, *args, output=None, diagnose=False, verbosity=1, **options):
        if diagnose:
            # List every invalid response only if --verbosity 2 or more asks for them
            self.report(ResearchExport().diagnose(max_examples=None if verbosity >= 2 else EXAMPLES_PER_SURVEY))
            return
        if not output:
            raise CommandError("Provide an output file with -o/--output, or use --diagnose")
        row_count = ResearchExport().write_xlsx(output)
        self.stdout.write(f"Wrote {row_count} responses to {output}")

    def report(self, diagnosis: ExportDiagnosis) -> None:
        def share(count: int) -> str:
            return f"{count / diagnosis.blank_count:.1%}" if diagnosis.blank_count else "0.0%"

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
            ("Overwritten by duplicate label", diagnosis.blank_overwritten),
        )
        for cause, count in causes:
            write(f"  {cause + ':':<41}{count} ({share(count)})")
        write(f"Answers overwritten by duplicate labels: {diagnosis.overwritten_answers}")

        write(f"\nResponses with answers missing from stored JSON: {sum(diagnosis.short_responses.values())}")
        for survey_id, count in sorted(diagnosis.short_responses.items()):
            write(f"  Survey {survey_id}: {count} of {diagnosis.rows_per_survey[survey_id]} responses")

        write(f"\nResponses failing JSON Schema validation: {sum(diagnosis.invalid_responses.values())}")
        for survey_id, count in sorted(diagnosis.invalid_responses.items()):
            write(f"  Survey {survey_id}: {count} of {diagnosis.rows_per_survey[survey_id]} responses")
            examples = diagnosis.invalid_examples[survey_id]
            for response_id, messages in examples:
                for message in messages:
                    write(f"    Response {response_id}: {message}")
            if count > len(examples):
                write(f"    ... and {count - len(examples)} more (use -v 2 to list all)")

        write(f"\nSurveys with duplicate question labels: {len(diagnosis.duplicate_labels)}")
        for survey_id, duplicates in sorted(diagnosis.duplicate_labels.items()):
            for label, count in duplicates.items():
                write(f"  Survey {survey_id}: {count} fields labelled {label!r}")
