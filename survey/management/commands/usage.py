import csv
import json

from django.core.management import BaseCommand, CommandError

from home.services.analytics import (
    CSV_REPORTS,
    DEFAULT_ACTIVE_DAYS,
    MAX_ACTIVE_DAYS,
    UsageAnalytics,
)
from survey.models import Survey


class Command(BaseCommand):
    """
    SORT Online usage report.

    Generate a summary of how the platform is being used, for impact reporting:

    * How many users and organisations, and how many are active
    * How many surveys were created and completed
    * How many responses were collected, and how many are shared
    * Who the biggest users and organisations are
    * Monthly trends
    """

    help = (
        "Generate a SORT Online usage report. With no arguments, outputs the original per-survey CSV;"
        " use --format for a text summary, the full JSON, or a CSV table."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            choices=("text", "json", "csv"),
            default=None,
            help="Output format. Omit for the original per-survey CSV (legacy column names)",
        )
        parser.add_argument(
            "--report",
            choices=CSV_REPORTS,
            default="surveys",
            help="Which table to output when --format=csv (default: surveys)",
        )
        parser.add_argument(
            "--active-days",
            type=int,
            default=DEFAULT_ACTIVE_DAYS,
            help=(
                "Window in days for an organisation to count as active,"
                f" 1 to {MAX_ACTIVE_DAYS} (default: {DEFAULT_ACTIVE_DAYS})"
            ),
        )

    def handle(self, *args, **options):
        if not 1 <= options["active_days"] <= MAX_ACTIVE_DAYS:
            raise CommandError(f"--active-days must be between 1 and {MAX_ACTIVE_DAYS}")
        if options["format"] is None:
            return self.write_legacy_csv()
        analytics = UsageAnalytics(active_days=options["active_days"])

        if options["format"] == "csv":
            analytics.write_csv(options["report"], self.stdout)
        elif options["format"] == "json":
            self.stdout.write(json.dumps(analytics.as_dict(), indent=2))
        else:
            self.write_text(analytics.as_dict())

    def write_legacy_csv(self):
        """The original output, kept unchanged for existing scripts."""
        writer = csv.writer(self.stdout, lineterminator="\n")
        writer.writerow(["Organisation", "Project", "Survey ID", "Survey", "Survey created at", "Responses"])
        for survey in Survey.objects.all():
            writer.writerow(
                (
                    survey.organisation,
                    survey.project,
                    survey.pk,
                    survey,
                    survey.created_at.isoformat(),
                    survey.survey_response.count(),
                )
            )

    def write_text(self, data: dict):
        summary = data["summary"]
        users = summary["users"]
        orgs = summary["organisations"]
        surveys = summary["surveys"]
        responses = summary["responses"]
        per_survey = data["responses_per_survey"]
        days = data["active_days"]

        lines = [
            f"SORT Online usage report ({data['generated_at']})",
            "",
            "Users",
            f"  Active accounts: {users['active']}",
            f"  Logged in (last {days} days): {users['logged_in_recently']}",
            f"  Suspended: {users['suspended']}",
            f"  Deleted: {users['deleted']}",
            "",
            "Organisations",
            f"  Total: {orgs['total']}",
            f"  Active (response in last {days} days): {orgs['active']}",
            f"  With multiple surveys: {orgs['with_multiple_surveys']}",
            "",
            f"Projects: {summary['projects']}",
            "",
            "Surveys",
            f"  Total: {surveys['total']}",
            f"  Collecting responses: {surveys['collecting']}",
            f"  With responses: {surveys['with_responses']}",
            f"  Completed (>{data['completed_survey_min_responses']} responses): {surveys['completed']}",
            f"  Sharing data: {surveys['shared']}",
            "",
            "Responses",
            f"  Total: {responses['total']}",
            f"  Shared: {responses['shared']}",
            f"  Last {days} days: {responses['recent']}",
            f"  Per survey (surveys with responses): min {per_survey['min']}, median {per_survey['median']},"
            f" mean {per_survey['mean']}, max {per_survey['max']}",
            "",
            "Top organisations (by responses)",
        ]
        for org in data["top_organisations"]:
            lines.append(f"  {org['responses']:>6}  {org['name']} ({org['surveys']} surveys, {org['members']} members)")
        lines += ["", "Top users (by responses to their projects)"]
        for user in data["top_users"]:
            lines.append(f"  {user['responses']:>6}  {user['name']} <{user['email']}> ({user['surveys']} surveys)")
        lines += ["", "Monthly trends (new this month / running total)"]
        lines.append(f"  {'Month':<8} {'Users':>11} {'Orgs':>11} {'Surveys':>11} {'Responses':>13}")
        for row in data["monthly_trends"]:
            cells = [f"{row[s]}/{row[s + '_total']}" for s in ("users", "organisations", "surveys", "responses")]
            lines.append(f"  {row['month']:<8} {cells[0]:>11} {cells[1]:>11} {cells[2]:>11} {cells[3]:>13}")

        self.stdout.write("\n".join(lines))
