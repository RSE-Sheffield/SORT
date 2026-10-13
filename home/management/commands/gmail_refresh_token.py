from django.core.management.base import BaseCommand, CommandError
from google_auth_oauthlib.flow import InstalledAppFlow

from home.checks.email import GMAIL_API_BACKEND

# Only allow SORT to send email, not to read or delete the mailbox's messages
# https://developers.google.com/workspace/gmail/api/auth/scopes
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


class Command(BaseCommand):
    help = (
        "Sign in to the sending Google account and print the OAuth2 settings "
        "for the Gmail API email backend. See 'Email settings' in "
        "docs/deployment.md."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--client-secrets",
            required=True,
            metavar="PATH",
            help="JSON file of the Desktop app OAuth client, downloaded from Google Cloud",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=0,
            help="Local port to receive Google's redirect on (default: any free port)",
        )
        parser.add_argument(
            "--no-browser",
            action="store_true",
            help="Print the sign-in URL instead of opening a web browser",
        )

    def handle(self, *args, **options):
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                options["client_secrets"], scopes=[GMAIL_SEND_SCOPE]
            )
        except FileNotFoundError:
            raise CommandError(f"File not found: {options['client_secrets']}")
        except ValueError as error:
            raise CommandError(
                f"{options['client_secrets']} is not a valid OAuth client "
                f"secrets file: {error} Download the JSON for an OAuth client "
                "of type 'Desktop app'."
            )

        credentials = flow.run_local_server(
            port=options["port"],
            open_browser=not options["no_browser"],
            # Ask for a refresh token, and force the consent screen so Google
            # issues a new one even if this account has authorised SORT before.
            access_type="offline",
            prompt="consent",
        )

        if not credentials.refresh_token:
            raise CommandError("Google did not return a refresh token.")

        self.stderr.write(
            "Add these lines to the .env file and store the values in the "
            "password manager:\n"
        )
        self.stdout.write(f"DJANGO_EMAIL_BACKEND={GMAIL_API_BACKEND}")
        self.stdout.write(f"DJANGO_GMAIL_API_CLIENT_ID={credentials.client_id}")
        self.stdout.write(f"DJANGO_GMAIL_API_CLIENT_SECRET={credentials.client_secret}")
        self.stdout.write(f"DJANGO_GMAIL_API_REFRESH_TOKEN={credentials.refresh_token}")
