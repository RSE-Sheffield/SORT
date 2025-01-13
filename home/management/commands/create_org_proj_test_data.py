from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from home.models import (
    User,
    Organisation,
    OrganisationMembership,
    Project,
    ProjectOrganisation,
)


class Command(BaseCommand):
    help = "Creates Organisation and Project test data"

    def handle(self, *args, **kwargs):
        # Create users
        admin = User.objects.create(
            email="admin@admin.com",
            password=make_password("admin"),
            first_name="Test-admin",
            last_name="User",
            is_staff=True,
            is_superuser=True,
        )

        # Create organisations
        org = Organisation.objects.create(name="Datavis Team")

        # Create memberships
        OrganisationMembership.objects.create(
            user=admin, organisation=org, role="ADMIN"
        )

        # Create projects
        project = Project.objects.create(name="Data Surveys 2025", created_by=admin)

        # Create project-org relationships
        ProjectOrganisation.objects.create(
            project=project, organisation=org, added_by=admin
        )

        self.stdout.write(self.style.SUCCESS("Successfully created Organisation and Project test data"))
