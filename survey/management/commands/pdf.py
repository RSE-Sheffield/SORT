from pathlib import Path

from django.conf import settings
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
    get_user_model,
)
from django.contrib.sessions.backends.db import SessionStore
from django.core.management import BaseCommand
from django.urls import reverse

from survey.models import Survey

User = get_user_model()


class Command(BaseCommand):
    """
    Export a survey report to PDF using Playwright headless browser.

    This command renders the /survey/{pk}/report page for a specific survey
    and exports it as a PDF file. Authentication is handled by creating a
    Django session programmatically and injecting it into the browser context.

    Requirements:
        pip install playwright
        playwright install chromium
    """

    help = "Export a survey report to PDF file"

    def add_arguments(self, parser):
        parser.add_argument(
            "survey_id",
            type=int,
            help="Survey ID to export (e.g., '1')",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="exports/reports",
            help="Output directory for PDF files (default: exports/reports)",
        )
        parser.add_argument(
            "--base-url",
            type=str,
            default="http://127.0.0.1:8000",
            help="Base URL for the Django server (default: http://127.0.0.1:8000)",
        )
        parser.add_argument(
            "--headless",
            action="store_true",
            default=True,
            help="Run browser in headless mode (default: True)",
        )

    def handle(self, *args, **options):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.stderr.write(
                self.style.ERROR(
                    "Playwright is not installed. Please install it with:\n"
                    "  pip install playwright\n"
                    "  playwright install chromium"
                )
            )
            return

        # Get the survey
        survey_id = options["survey_id"]
        try:
            survey = Survey.objects.get(pk=survey_id)
        except Survey.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"Survey with ID {survey_id} not found.")
            )
            return

        # Create output directory
        output_dir = Path(options["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        base_url = options["base_url"]
        headless = options["headless"]

        self.stdout.write(
            f"Exporting survey report for Survey {survey.pk}: {survey.name}"
        )
        self.stdout.write(f"Output directory: {output_dir.absolute()}")

        # Get a superuser for authentication
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            self.stderr.write(
                self.style.ERROR(
                    "No superuser found. Please create a superuser to authenticate."
                )
            )
            return

        # Create Django session with superuser authentication
        self.stdout.write("Creating authenticated session...")
        session = SessionStore()
        session[SESSION_KEY] = str(superuser.pk)
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[HASH_SESSION_KEY] = superuser.get_session_auth_hash()
        session.save()

        # Create session cookie for Playwright
        session_cookie = {
            "name": settings.SESSION_COOKIE_NAME,
            "value": session.session_key,
            "domain": "127.0.0.1",
            "path": "/",
            "httpOnly": True,
            "secure": False,  # False for local development
            "sameSite": "Lax",
        }

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()

            # Inject the session cookie
            context.add_cookies([session_cookie])

            page = context.new_page()
            self.stdout.write(self.style.SUCCESS("Authenticated session created"))

            # Export the survey report
            try:
                self.stdout.write(f"Processing Survey {survey.pk}: {survey.name}...")

                # Navigate to report page
                report_url = (
                    f"{base_url}{reverse('survey_report', kwargs={'pk': survey.pk})}"
                )
                page.goto(report_url, wait_until="networkidle")

                # Check for errors
                if (
                    page.locator("text=/error|not found|permission denied/i").count()
                    > 0
                ):
                    self.stderr.write(
                        self.style.WARNING(
                            f"Warning: Possible error on page for Survey {survey.pk}"
                        )
                    )

                # Generate PDF filename
                filename = f"survey_{survey.pk}_{survey.reference_number}.pdf"
                output_path = output_dir / filename

                # Export to PDF
                page.pdf(
                    path=str(output_path),
                    format="A4",
                    print_background=True,
                    margin={
                        "top": "1cm",
                        "right": "1cm",
                        "bottom": "1cm",
                        "left": "1cm",
                    },
                )

                self.stdout.write(self.style.SUCCESS(f"Exported: {output_path}"))

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"Failed to export Survey {survey.pk}: {str(e)}")
                )
            finally:
                browser.close()

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted! Exported report to {output_dir.absolute()}"
            )
        )
