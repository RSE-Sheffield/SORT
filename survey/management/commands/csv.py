import sys

from django.conf import settings
from django.core.management import BaseCommand

from survey.models import Survey


class Command(BaseCommand):
    """
    Survey CSV export
    """

    help = "Export a survey response to a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("survey_id", type=int, help="Survey primary key (integer)")

    def handle(self, *args, **options):
        survey = Survey.objects.get(pk=options["survey_id"])
        self.stdout.reconfigure(encoding=settings.DEFAULT_CHARSET)
        self.stdout.write(survey.to_csv())
