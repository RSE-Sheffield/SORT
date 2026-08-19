from django.core.exceptions import ValidationError
from django.core.management import BaseCommand

from survey.models import Survey


class Command(BaseCommand):
    help = "Validate all survey response answers against their survey's JSON Schema"

    def add_arguments(self, parser):
        parser.add_argument(
            "--survey",
            type=int,
            dest="survey_id",
            help="Only validate the responses of this survey (by primary key)",
        )

    def handle(self, *args, **options):
        errors = 0
        total = 0
        surveys = Survey.objects.prefetch_related("survey_response")
        survey_id = options.get("survey_id")
        if survey_id is not None:
            surveys = surveys.filter(pk=survey_id)
        for survey in surveys.iterator(chunk_size=100):
            for response in survey.survey_response.all():
                total += 1
                try:
                    response.validate()
                except ValidationError as exc:
                    errors += 1
                    for message in exc.messages:
                        self.stderr.write(
                            f"Survey {survey.pk} / Response {response.pk}: {message}"
                        )
        self.stdout.write(f"Validated {total} responses - {errors} error(s)")
        if errors:
            exit(1)
