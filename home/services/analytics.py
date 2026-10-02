"""
Usage analytics service.

Aggregates platform-wide figures about how SORT Online is being used (users,
organisations, surveys, responses and their trends over time) for impact
reporting. See GitHub issue #726.

These are read-only, platform-wide aggregates rather than user-scoped
operations, so methods are not gated with `@requires_permission`. Access is
enforced by the callers: the staff console (`StaffRequiredMixin`) and the
`usage` management command (server shell access).
"""

import csv
import statistics
from datetime import date, datetime, timedelta
from typing import IO, Optional

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from home.constants import DELETED_ACCOUNT_EMAIL_DOMAIN
from home.models import Organisation, Project, User
from survey.models import Survey, SurveyResponse

# A survey counts as "completed" (i.e. it has seen real use) when it has
# strictly more than this many responses.
COMPLETED_SURVEY_MIN_RESPONSES = 10
# An organisation is "active" if it has received a response within this many days.
DEFAULT_ACTIVE_DAYS = 90
# Upper bound for the active window (~10 years); larger values overflow date arithmetic.
MAX_ACTIVE_DAYS = 3650
# Number of rows in the "biggest users/organisations" leaderboards.
TOP_N = 10

TREND_SERIES = ("users", "organisations", "surveys", "responses")
# Column names for each tabular report (these match the dictionary keys returned by the service)
CSV_FIELDS = {
    "surveys": [
        "organisation",
        "project",
        "survey_id",
        "survey",
        "created_at",
        "responses",
        "collecting",
        "shared",
        "completed",
    ],
    "trends": ["month", *TREND_SERIES, *(f"{series}_total" for series in TREND_SERIES)],
    "organisations": ["id", "name", "responses", "surveys", "members", "created_at"],
}
CSV_REPORTS = tuple(CSV_FIELDS)


def _month_key(value: datetime | date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def _next_month(value: date) -> date:
    return date(value.year + value.month // 12, value.month % 12 + 1, 1)


class UsageAnalytics:
    """
    Platform-wide usage figures.

    :param active_days: The window used to decide whether an organisation is active.
    :param now: The reference time (defaults to the current time; injectable for tests).
    """

    def __init__(self, active_days: int = DEFAULT_ACTIVE_DAYS, now: Optional[datetime] = None):
        self.active_days = active_days
        self.now = now or timezone.now()

    @property
    def active_since(self) -> datetime:
        return self.now - timedelta(days=self.active_days)

    def summary(self) -> dict:
        """Headline counts."""
        deleted = Q(email__endswith=f"@{DELETED_ACCOUNT_EMAIL_DOMAIN}")
        users = User.objects.aggregate(
            total=Count("pk"),
            active=Count("pk", filter=Q(is_active=True)),
            suspended=Count("pk", filter=Q(is_active=False) & ~deleted),
            deleted=Count("pk", filter=deleted),
            logged_in_recently=Count(
                "pk", filter=Q(is_active=True, last_login__gte=self.active_since)
            ),
        )
        surveys_with_counts = Survey.objects.annotate(n=Count("survey_response"))
        responses = SurveyResponse.objects.aggregate(
            total=Count("pk"),
            shared=Count("pk", filter=Q(survey__is_shared=True)),
            recent=Count("pk", filter=Q(created_at__gte=self.active_since)),
        )
        return {
            "users": users,
            "organisations": {
                "total": Organisation.objects.count(),
                "active": Organisation.objects.filter(
                    projects__survey__survey_response__created_at__gte=self.active_since
                )
                .distinct()
                .count(),
                "with_multiple_surveys": Organisation.objects.annotate(
                    n=Count("projects__survey", distinct=True)
                )
                .filter(n__gte=2)
                .count(),
            },
            "projects": Project.objects.count(),
            "surveys": {
                "total": Survey.objects.count(),
                "collecting": Survey.objects.filter(is_active=True).count(),
                "with_responses": surveys_with_counts.filter(n__gt=0).count(),
                "completed": surveys_with_counts.filter(n__gt=COMPLETED_SURVEY_MIN_RESPONSES).count(),
                "shared": Survey.objects.filter(is_shared=True).count(),
            },
            "responses": responses,
        }

    def responses_per_survey(self) -> dict:
        """Distribution of response counts, over surveys that have at least one response."""
        counts = sorted(
            Survey.objects.annotate(n=Count("survey_response"))
            .filter(n__gt=0)
            .values_list("n", flat=True)
        )
        if not counts:
            return {"surveys": 0, "min": 0, "median": 0, "mean": 0, "max": 0}
        return {
            "surveys": len(counts),
            "min": counts[0],
            "median": statistics.median(counts),
            "mean": round(statistics.mean(counts), 1),
            "max": counts[-1],
        }

    def top_organisations(self, n: Optional[int] = TOP_N) -> list[dict]:
        """
        The organisations that have collected the most responses.

        :param n: Maximum number of rows, or None for every organisation (including those without responses).
        """
        organisations = Organisation.objects.annotate(
            responses=Count("projects__survey__survey_response", distinct=True),
            surveys=Count("projects__survey", distinct=True),
            member_count=Count("members", distinct=True),
        ).order_by("-responses", "name")
        if n is not None:
            organisations = organisations.filter(responses__gt=0)[:n]
        return [
            {
                "id": org.pk,
                "name": org.name,
                "responses": org.responses,
                "surveys": org.surveys,
                "members": org.member_count,
                "created_at": org.created_at.isoformat(),
            }
            for org in organisations
        ]

    def top_users(self, n: int = TOP_N) -> list[dict]:
        """The users whose projects have collected the most responses."""
        users = (
            User.objects.filter(is_active=True)
            .annotate(
                projects=Count("project", distinct=True),
                surveys=Count("project__survey", distinct=True),
                responses=Count("project__survey__survey_response", distinct=True),
            )
            .filter(responses__gt=0)
            .order_by("-responses", "email")[:n]
        )
        return [
            {
                "id": user.pk,
                "name": f"{user.first_name} {user.last_name}".strip(),
                "email": user.email,
                "projects": user.projects,
                "surveys": user.surveys,
                "responses": user.responses,
            }
            for user in users
        ]

    def monthly_trends(self) -> list[dict]:
        """
        New users, organisations, surveys and responses per calendar month, with
        running totals, from the first month with any activity up to the current month.
        Months with no activity are included with zero counts.
        """
        sources = {
            "users": (User.objects, "date_joined"),
            "organisations": (Organisation.objects, "created_at"),
            "surveys": (Survey.objects, "created_at"),
            "responses": (SurveyResponse.objects, "created_at"),
        }
        counts: dict[str, dict[str, int]] = {}
        for series, (manager, field) in sources.items():
            rows = (
                manager.annotate(month=TruncMonth(field))
                .values("month")
                .annotate(n=Count("pk"))
                .order_by()
            )
            counts[series] = {_month_key(row["month"]): row["n"] for row in rows}

        months = sorted({key for series in counts.values() for key in series})
        if not months:
            return []
        year, month = map(int, months[0].split("-"))
        current = date(year, month, 1)
        end = timezone.localtime(self.now).date().replace(day=1)

        trends = []
        totals = dict.fromkeys(TREND_SERIES, 0)
        while current <= end:
            key = _month_key(current)
            row = {"month": key}
            for series in TREND_SERIES:
                value = counts[series].get(key, 0)
                totals[series] += value
                row[series] = value
                row[f"{series}_total"] = totals[series]
            trends.append(row)
            current = _next_month(current)
        return trends

    def per_survey_rows(self) -> list[dict]:
        """One row per survey with its response count."""
        surveys = (
            Survey.objects.select_related("project__organisation")
            .annotate(responses=Count("survey_response"))
            .order_by("pk")
        )
        return [
            {
                "organisation": survey.project.organisation.name,
                "project": survey.project.name,
                "survey_id": survey.pk,
                "survey": survey.name,
                "created_at": survey.created_at.isoformat(),
                "responses": survey.responses,
                "collecting": survey.is_active,
                "shared": survey.is_shared,
                "completed": survey.responses > COMPLETED_SURVEY_MIN_RESPONSES,
            }
            for survey in surveys
        ]

    def as_dict(self) -> dict:
        """Every figure, as a JSON-serialisable dictionary."""
        return {
            "generated_at": self.now.isoformat(),
            "active_days": self.active_days,
            "completed_survey_min_responses": COMPLETED_SURVEY_MIN_RESPONSES,
            "summary": self.summary(),
            "responses_per_survey": self.responses_per_survey(),
            "top_organisations": self.top_organisations(),
            "top_users": self.top_users(),
            "monthly_trends": self.monthly_trends(),
        }

    def write_csv(self, report: str, file: IO[str]) -> None:
        """
        Write one tabular report as CSV.

        :param report: One of `CSV_REPORTS`.
        :param file: A text stream to write to.
        """
        if report == "surveys":
            rows = self.per_survey_rows()
        elif report == "trends":
            rows = self.monthly_trends()
        elif report == "organisations":
            rows = self.top_organisations(n=None)
        else:
            raise ValueError(f"Unknown report '{report}'. Choose from: {', '.join(CSV_REPORTS)}")
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS[report], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
