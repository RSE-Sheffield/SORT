from django.core.exceptions import ValidationError
from django.core.management import BaseCommand

from survey.models import Survey


class Command(BaseCommand):
    help = "Validate all survey response answers against their survey's JSON Schema"

    def handle(self, *args, **options):
        errors = 0
        total = 0
        for survey in Survey.objects.prefetch_related("survey_response").iterator(chunk_size=100):
            for response in survey.survey_response.all():
                total += 1
                try:
                    response.validate()
                except ValidationError as exc:
                    errors += 1
                    self.stderr.write(
                        f"Survey {survey.pk} / Response {response.pk}: {exc.message}"
                    )
        self.stdout.write(f"Validated {total} responses — {errors} error(s)")
        if errors:
            exit(1)
