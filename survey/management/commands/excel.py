from pathlib import Path

from django.core.management import BaseCommand

from survey.models import Survey


class Command(BaseCommand):
    """
    Survey Excel export
    """

    help = "Export a survey's responses to an Excel workbook file"

    def add_arguments(self, parser):
        parser.add_argument("survey_id", type=int, help="Survey primary key (integer)")
        parser.add_argument(
            "-o",
            "--output",
            type=str,
            default=None,
            help="Output filename (default: survey_<id>_responses.xlsx)"
        )

    def handle(self, *args, **options):
        survey_id = options["survey_id"]

        try:
            survey = Survey.objects.get(pk=survey_id)
        except Survey.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"Survey with ID {survey_id} does not exist")
            )
            return

        # Determine output filename
        if options["output"]:
            output_path = Path(options["output"])
        else:
            output_path = Path(f"survey_{survey_id}_responses.xlsx")

        # Get Excel data from the survey model
        excel_data = survey.to_excel()

        # Write to file
        with output_path.open("wb") as file:
            file.write(excel_data)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully exported {survey.responses_count} response(s) "
                f"from survey '{survey.name}' to {output_path}"
            )
        )
