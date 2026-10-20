import io

from django.core.management import call_command
from django.db.models import ProtectedError

import SORT.test.test_case
from home.models import OrganisationMembership, User
from SORT.test.model_factory import (
    OrganisationMembershipFactory,
    OrganisationFactory,
    ProjectFactory,
    UserFactory,
)


class AuditNullableFksCommandTestCase(SORT.test.test_case.ServiceTestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.organisation = OrganisationFactory()
        # OrganisationFactory creates an admin membership without added_by;
        # fill it in so each test controls which NULL rows exist.
        OrganisationMembership.objects.update(added_by=self.user)

    def _call(self):
        stdout = io.StringIO()
        call_command("audit_nullable_fks", stdout=stdout, stderr=io.StringIO())
        return stdout.getvalue()

    def test_reports_clean_when_no_nulls(self):
        ProjectFactory(organisation=self.organisation, created_by=self.user)
        OrganisationMembershipFactory(
            organisation=self.organisation, user=self.user, added_by=self.user
        )

        output = self._call()

        self.assertIn("Project.created_by: no NULL rows", output)
        self.assertIn("OrganisationMembership.added_by: no NULL rows", output)
        self.assertIn("Safe to make these fields non-nullable.", output)

    def test_reports_null_project_creators(self):
        project = ProjectFactory(organisation=self.organisation, created_by=None)

        output = self._call()

        self.assertIn(f"Project.created_by: 1 NULL row(s); first 1 ids: [{project.pk}]", output)
        self.assertNotIn("Safe to make these fields non-nullable.", output)

    def test_reports_null_membership_adders(self):
        membership = OrganisationMembershipFactory(
            organisation=self.organisation, user=self.user, added_by=None
        )

        output = self._call()

        self.assertIn(
            f"OrganisationMembership.added_by: 1 NULL row(s); first 1 ids: [{membership.pk}]",
            output,
        )
        self.assertNotIn("Safe to make these fields non-nullable.", output)

    def test_deleting_a_user_who_created_a_project_is_protected(self):
        ProjectFactory(organisation=self.organisation, created_by=self.user)

        with self.assertRaises(ProtectedError):
            User.objects.get(pk=self.user.pk).delete()
