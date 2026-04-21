import sys
import csv

from django.core.management import BaseCommand

from survey.models import Survey


class Command(BaseCommand):
    """
    SORT Online usage report.

    Generate a summary of how the platform is being used:

    * How many organisations signed up
    * How many surveys created
    * How many responses were collected
    """

    help = "Generate a SORT Online usage report in CSV format."

    def handle(self, *args, **options):
        """
        Generate CSV output
        """
        writer = csv.writer(sys.stdout, lineterminator="\n")
        # Header
        writer.writerow(
            [
                "Organisation",
                "Project",
                "Survey ID",
                "Survey",
                "Survey created at",
                "Responses",
            ]
        )
        # Generate one row per survey
        for survey in Survey.objects.all():
            row = (
                survey.organisation,
                survey.project,
                survey.pk,
                survey,
                survey.created_at.isoformat(),
                survey.survey_response.count(),
            )
            writer.writerow(row)
