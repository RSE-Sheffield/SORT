from django.core.management.base import BaseCommand

from home.models import OrganisationMembership, Project

SAMPLE_SIZE = 20


class Command(BaseCommand):
    help = (
        "Report rows where Project.created_by or OrganisationMembership.added_by "
        "is NULL. Read-only. Run before making those fields non-nullable."
    )

    def handle(self, *args, **options):
        checks = [
            ("Project.created_by", Project.objects.filter(created_by__isnull=True)),
            (
                "OrganisationMembership.added_by",
                OrganisationMembership.objects.filter(added_by__isnull=True),
            ),
        ]

        any_null = False
        for label, queryset in checks:
            count = queryset.count()
            if not count:
                self.stdout.write(f"{label}: no NULL rows")
                continue

            any_null = True
            ids = list(queryset.order_by("pk").values_list("pk", flat=True)[:SAMPLE_SIZE])
            self.stdout.write(
                f"{label}: {count} NULL row(s); first {len(ids)} ids: {ids}"
            )

        if not any_null:
            self.stdout.write("Safe to make these fields non-nullable.")
