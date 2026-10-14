"""
Test that the short code migration back-fills existing invitations without
altering their tokens, so that previously shared long links keep working.
"""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from SORT.test.model_factory import SurveyFactory


class TestShortCodeMigration(TransactionTestCase):
    migrate_from = [("survey", "0030_merge_20260217_1045")]
    migrate_to = [("survey", "0031_invitation_short_code")]

    def test_existing_invitations_backfilled(self):
        survey = SurveyFactory()

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        OldInvitation = old_apps.get_model("survey", "Invitation")
        tokens = {
            OldInvitation.objects.create(survey_id=survey.pk, token=f"legacy-token-{i}").token
            for i in range(3)
        }

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(self.migrate_to)
        new_apps = executor.loader.project_state(self.migrate_to).apps
        NewInvitation = new_apps.get_model("survey", "Invitation")

        invitations = NewInvitation.objects.filter(token__in=tokens)
        self.assertEqual(set(invitations.values_list("token", flat=True)), tokens)
        codes = [invitation.short_code for invitation in invitations]
        self.assertNotIn(None, codes)
        self.assertEqual(len(set(codes)), len(codes))
