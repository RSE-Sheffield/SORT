"""
Test the usage analytics service (issue #726).
"""

import csv
import io
from datetime import datetime, timedelta, timezone

import SORT.test.test_case
from home.constants import DELETED_ACCOUNT_EMAIL_DOMAIN
from home.models import Organisation, User
from home.services.analytics import COMPLETED_SURVEY_MIN_RESPONSES, CSV_FIELDS, UsageAnalytics
from SORT.test.model_factory import OrganisationFactory, ProjectFactory, SurveyFactory, UserFactory
from survey.models import Survey, SurveyResponse

NOW = datetime(2026, 3, 15, 12, tzinfo=timezone.utc)


def add_responses(survey: Survey, count: int, created_at: datetime = NOW) -> None:
    SurveyResponse.objects.bulk_create(SurveyResponse(survey=survey, answers=[]) for _ in range(count))
    # created_at is auto_now_add, so backdate it after creation
    SurveyResponse.objects.filter(survey=survey).update(created_at=created_at)


class UsageAnalyticsTestCase(SORT.test.test_case.ServiceTestCase):

    def setUp(self):
        super().setUp()
        self.analytics = UsageAnalytics(active_days=90, now=NOW)

    def test_completed_survey_threshold(self):
        """A survey is completed only with strictly more than the threshold number of responses."""
        add_responses(SurveyFactory(), COMPLETED_SURVEY_MIN_RESPONSES)
        add_responses(SurveyFactory(), COMPLETED_SURVEY_MIN_RESPONSES + 1)
        SurveyFactory()

        surveys = self.analytics.summary()["surveys"]
        self.assertEqual(surveys["total"], 3)
        self.assertEqual(surveys["with_responses"], 2)
        self.assertEqual(surveys["completed"], 1)

    def test_active_organisation_window(self):
        """Organisations are active only if they received a response within the window."""
        recent = SurveyFactory()
        add_responses(recent, 1, created_at=NOW - timedelta(days=10))
        stale = SurveyFactory()
        add_responses(stale, 1, created_at=NOW - timedelta(days=200))
        OrganisationFactory()

        orgs = self.analytics.summary()["organisations"]
        self.assertEqual(orgs["total"], Organisation.objects.count())
        self.assertEqual(orgs["active"], 1)
        self.assertEqual(UsageAnalytics(active_days=365, now=NOW).summary()["organisations"]["active"], 2)

    def test_active_organisation_counted_once(self):
        """An organisation with many recent responses is only counted once."""
        survey = SurveyFactory()
        SurveyFactory(project=survey.project)
        add_responses(survey, 5)
        self.assertEqual(self.analytics.summary()["organisations"]["active"], 1)

    def test_organisations_with_multiple_surveys(self):
        project = ProjectFactory()
        SurveyFactory(project=project)
        SurveyFactory(project=ProjectFactory(organisation=project.organisation))
        SurveyFactory()

        self.assertEqual(self.analytics.summary()["organisations"]["with_multiple_surveys"], 1)

    def test_user_account_states(self):
        """Suspended and deleted accounts are counted separately."""
        UserFactory(is_active=False)
        UserFactory(is_active=False, email=f"deleted-1@{DELETED_ACCOUNT_EMAIL_DOMAIN}")

        users = self.analytics.summary()["users"]
        self.assertEqual(users["total"], User.objects.count())
        self.assertEqual(users["active"], User.objects.filter(is_active=True).count())
        self.assertEqual(users["suspended"], 1)
        self.assertEqual(users["deleted"], 1)

    def test_shared_responses(self):
        add_responses(SurveyFactory(is_shared=True), 3)
        add_responses(SurveyFactory(is_shared=False), 2)

        responses = self.analytics.summary()["responses"]
        self.assertEqual(responses["total"], 5)
        self.assertEqual(responses["shared"], 3)

    def test_responses_per_survey(self):
        for count in (1, 2, 9):
            add_responses(SurveyFactory(), count)
        SurveyFactory()

        self.assertEqual(
            self.analytics.responses_per_survey(),
            {"surveys": 3, "min": 1, "median": 2, "mean": 4.0, "max": 9},
        )

    def test_responses_per_survey_empty(self):
        self.assertEqual(self.analytics.responses_per_survey()["surveys"], 0)

    def test_top_organisations(self):
        big = SurveyFactory()
        add_responses(big, 5)
        add_responses(SurveyFactory(project=big.project), 2)
        small = SurveyFactory()
        add_responses(small, 1)
        OrganisationFactory()

        top = self.analytics.top_organisations()
        self.assertEqual([row["name"] for row in top], [big.organisation.name, small.organisation.name])
        self.assertEqual(top[0]["responses"], 7)
        self.assertEqual(top[0]["surveys"], 2)
        # Every organisation is included when there's no limit
        self.assertEqual(len(self.analytics.top_organisations(n=None)), Organisation.objects.count())

    def test_top_users(self):
        creator = UserFactory()
        survey = SurveyFactory(project=ProjectFactory(created_by=creator))
        add_responses(survey, 4)

        top = self.analytics.top_users()
        self.assertEqual(len(top), 1)
        self.assertEqual(top[0]["email"], creator.email)
        self.assertEqual(top[0]["responses"], 4)
        self.assertEqual(top[0]["surveys"], 1)

    def test_monthly_trends_fill_gaps(self):
        """Months without activity are included, and running totals accumulate."""
        survey = SurveyFactory()
        User.objects.update(date_joined=datetime(2025, 12, 1, tzinfo=timezone.utc))
        Organisation.objects.update(created_at=datetime(2025, 12, 1, tzinfo=timezone.utc))
        Survey.objects.update(created_at=datetime(2026, 1, 10, tzinfo=timezone.utc))
        add_responses(survey, 3, created_at=datetime(2026, 3, 1, tzinfo=timezone.utc))

        trends = self.analytics.monthly_trends()
        self.assertEqual([row["month"] for row in trends], ["2025-12", "2026-01", "2026-02", "2026-03"])
        self.assertEqual([row["surveys"] for row in trends], [0, 1, 0, 0])
        self.assertEqual([row["responses"] for row in trends], [0, 0, 0, 3])
        self.assertEqual([row["surveys_total"] for row in trends], [0, 1, 1, 1])
        self.assertEqual(trends[-1]["users_total"], User.objects.count())
        self.assertEqual(trends[-1]["organisations_total"], Organisation.objects.count())

    def test_write_csv(self):
        add_responses(SurveyFactory(), COMPLETED_SURVEY_MIN_RESPONSES + 1)
        for report, fields in CSV_FIELDS.items():
            with self.subTest(report=report):
                output = io.StringIO()
                self.analytics.write_csv(report, output)
                rows = list(csv.DictReader(io.StringIO(output.getvalue())))
                self.assertGreater(len(rows), 0)
                self.assertEqual(list(rows[0]), fields)

        output = io.StringIO()
        self.analytics.write_csv("surveys", output)
        row = next(csv.DictReader(io.StringIO(output.getvalue())))
        self.assertEqual(row["completed"], "True")

    def test_write_csv_unknown_report(self):
        with self.assertRaises(ValueError):
            self.analytics.write_csv("nonsense", io.StringIO())

    def test_as_dict_empty_database(self):
        """Everything works with no data."""
        SurveyResponse.objects.all().delete()
        Survey.objects.all().delete()
        data = self.analytics.as_dict()
        self.assertEqual(data["summary"]["surveys"]["total"], 0)
        self.assertEqual(data["top_organisations"], [])
