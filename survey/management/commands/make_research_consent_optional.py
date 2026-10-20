from django.core.management import BaseCommand

from survey.models import RESEARCH_CONSENT_FIELD_NAME, Survey


def find_research_consent_field(config: dict | None) -> dict | None:
    """Find the research consent question in the first (consent) section."""
    sections = (config or {}).get("sections") or []
    fields = sections[0].get("fields", []) if sections else []
    return next(
        (f for f in fields if f.get("name") == RESEARCH_CONSENT_FIELD_NAME),
        None,
    )


class Command(BaseCommand):
    help = (
        "Make the research consent question optional in existing surveys, "
        "whose consent section was copied from the template when they were created. "
        "Its description is replaced with the current template wording."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--survey",
            type=int,
            dest="survey_id",
            help="Only update this survey (by primary key)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report the surveys that would change without saving them",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        updated = 0
        skipped = 0
        surveys = Survey.objects.all()
        survey_id = options.get("survey_id")
        if survey_id is not None:
            surveys = surveys.filter(pk=survey_id)

        template_field = None
        for survey in surveys.iterator(chunk_size=100):
            field = find_research_consent_field(survey.survey_config)
            if field is None or not field.get("required"):
                skipped += 1
                continue

            if template_field is None:
                template_field = find_research_consent_field(
                    survey.consent_config_default
                )
            updated += 1
            self.stdout.write(
                f"{'Would update' if dry_run else 'Updating'} survey {survey.pk}"
            )
            if not dry_run:
                field["required"] = False
                # Replace the old "you must agree" wording so it doesn't contradict
                field["description"] = template_field["description"]
                survey.save(update_fields=["survey_config"])

        verb = "would be updated" if dry_run else "updated"
        self.stdout.write(f"{updated} survey(s) {verb}, {skipped} skipped")
