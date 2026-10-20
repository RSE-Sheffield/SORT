from django.core.management.base import BaseCommand, CommandError

from home.models import Organisation, User
from home.services import organisation_service
from home.services.organisation import plan_organisation_merge


class Command(BaseCommand):
    help = (
        "Merge one organisation into another: move its projects and "
        "memberships, then delete it."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "source_id",
            type=int,
            help="ID of the organisation to merge (will be deleted)",
        )
        parser.add_argument(
            "target_id", type=int, help="ID of the organisation to merge into"
        )
        parser.add_argument(
            "--actioned-by",
            required=True,
            metavar="EMAIL",
            help="Email of the staff user performing the merge (recorded in the audit log)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would happen without making any changes",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip the confirmation prompt",
        )

    def handle(self, *args, **options):
        try:
            source = Organisation.objects.get(pk=options["source_id"])
        except Organisation.DoesNotExist:
            raise CommandError(f"No organisation found with id {options['source_id']}")

        try:
            target = Organisation.objects.get(pk=options["target_id"])
        except Organisation.DoesNotExist:
            raise CommandError(f"No organisation found with id {options['target_id']}")

        try:
            actioned_by = User.objects.get(email__iexact=options["actioned_by"])
        except User.DoesNotExist:
            raise CommandError(f"No user found with email '{options['actioned_by']}'")

        if not (actioned_by.is_staff or actioned_by.is_superuser):
            raise CommandError(
                f"User '{actioned_by.email}' is not staff and cannot perform an "
                f"organisation merge"
            )

        try:
            plan = plan_organisation_merge(source, target)
        except ValueError as exc:
            raise CommandError(str(exc))

        self.stdout.write(plan.describe())

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run - no changes made"))
            return

        if not options["yes"]:
            confirmation = input(
                f"Merge '{source.name}' (id={source.pk}) into '{target.name}' "
                f"(id={target.pk})? This deletes '{source.name}'. "
                f"Type 'yes' to continue: "
            )
            if confirmation != "yes":
                raise CommandError("Aborted")

        organisation_service.merge_organisations(actioned_by, source, target)
        self.stdout.write(self.style.SUCCESS(f"Merged '{source.name}' into '{target.name}'"))
