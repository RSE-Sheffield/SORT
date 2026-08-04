"""
Test the `merge_organisations` management command (issue #676).
"""

import io
import unittest.mock

from django.core.management import call_command
from django.core.management.base import CommandError

import SORT.test.test_case
from home.models import Organisation
from SORT.test.model_factory import OrganisationFactory, ProjectFactory


class MergeOrganisationsCommandTestCase(SORT.test.test_case.ServiceTestCase):

    def setUp(self):
        super().setUp()
        self.source = OrganisationFactory()
        self.target = OrganisationFactory()

    def _call(self, *args, **options):
        stdout = io.StringIO()
        call_command("merge_organisations", *args, stdout=stdout, stderr=io.StringIO(), **options)
        return stdout.getvalue()

    def test_dry_run_makes_no_changes(self):
        project = ProjectFactory(organisation=self.source)

        output = self._call(
            self.source.pk,
            self.target.pk,
            actioned_by=self.superuser.email,
            dry_run=True,
        )

        self.assertIn("Dry run", output)
        project.refresh_from_db()
        self.assertEqual(self.source, project.organisation)
        self.assertTrue(Organisation.objects.filter(pk=self.source.pk).exists())

    def test_missing_actioned_by_raises(self):
        with self.assertRaises(CommandError):
            self._call(
                self.source.pk,
                self.target.pk,
                actioned_by="not-a-real-user@sort.com",
                dry_run=True,
            )

    def test_non_staff_actioned_by_raises(self):
        with self.assertRaises(CommandError):
            self._call(
                self.source.pk,
                self.target.pk,
                actioned_by=self.user.email,
                dry_run=True,
            )

    def test_yes_skips_confirmation_and_merges(self):
        project = ProjectFactory(organisation=self.source)

        self._call(self.source.pk, self.target.pk, actioned_by=self.superuser.email, yes=True)

        project.refresh_from_db()
        self.assertEqual(self.target, project.organisation)
        self.assertFalse(Organisation.objects.filter(pk=self.source.pk).exists())

    def test_unconfirmed_prompt_aborts(self):
        project = ProjectFactory(organisation=self.source)

        with unittest.mock.patch("builtins.input", return_value="no"):
            with self.assertRaises(CommandError):
                self._call(self.source.pk, self.target.pk, actioned_by=self.superuser.email)

        project.refresh_from_db()
        self.assertEqual(self.source, project.organisation)
        self.assertTrue(Organisation.objects.filter(pk=self.source.pk).exists())
