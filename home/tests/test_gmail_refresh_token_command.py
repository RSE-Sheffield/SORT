"""
Test the `gmail_refresh_token` management command (issue #754).
"""

import io
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

FROM_CLIENT_SECRETS_FILE = (
    "home.management.commands.gmail_refresh_token."
    "InstalledAppFlow.from_client_secrets_file"
)


class GmailRefreshTokenCommandTestCase(SimpleTestCase):
    def setUp(self):
        self.credentials = mock.Mock(
            client_id="test-client-id",
            client_secret="test-client-secret",
            refresh_token="test-refresh-token",
        )
        self.flow = mock.Mock()
        self.flow.run_local_server.return_value = self.credentials

    def _call(self, *args):
        stdout = io.StringIO()
        call_command(
            "gmail_refresh_token",
            "--client-secrets",
            "client_secret.json",
            *args,
            stdout=stdout,
            stderr=io.StringIO(),
        )
        return stdout.getvalue()

    def test_prints_env_settings(self):
        with mock.patch(FROM_CLIENT_SECRETS_FILE, return_value=self.flow):
            output = self._call()

        self.assertEqual(
            output.splitlines(),
            [
                "DJANGO_EMAIL_BACKEND=gmailapi_backend.mail.GmailBackend",
                "DJANGO_GMAIL_API_CLIENT_ID=test-client-id",
                "DJANGO_GMAIL_API_CLIENT_SECRET=test-client-secret",
                "DJANGO_GMAIL_API_REFRESH_TOKEN=test-refresh-token",
            ],
        )

    def test_requests_send_only_scope_and_a_refresh_token(self):
        with mock.patch(
            FROM_CLIENT_SECRETS_FILE, return_value=self.flow
        ) as from_client_secrets_file:
            self._call()

        from_client_secrets_file.assert_called_once_with(
            "client_secret.json",
            scopes=["https://www.googleapis.com/auth/gmail.send"],
        )
        kwargs = self.flow.run_local_server.call_args.kwargs
        self.assertEqual(kwargs["access_type"], "offline")
        self.assertEqual(kwargs["prompt"], "consent")
        self.assertTrue(kwargs["open_browser"])

    def test_no_browser_and_port_options(self):
        with mock.patch(FROM_CLIENT_SECRETS_FILE, return_value=self.flow):
            self._call("--no-browser", "--port", "8088")

        kwargs = self.flow.run_local_server.call_args.kwargs
        self.assertFalse(kwargs["open_browser"])
        self.assertEqual(kwargs["port"], 8088)

    def test_missing_client_secrets_file(self):
        with mock.patch(FROM_CLIENT_SECRETS_FILE, side_effect=FileNotFoundError):
            with self.assertRaisesMessage(CommandError, "File not found"):
                self._call()

    def test_invalid_client_secrets_file(self):
        with mock.patch(
            FROM_CLIENT_SECRETS_FILE, side_effect=ValueError("Client secrets must be")
        ):
            with self.assertRaisesMessage(CommandError, "Desktop app"):
                self._call()

    def test_no_refresh_token_returned(self):
        self.credentials.refresh_token = None
        with mock.patch(FROM_CLIENT_SECRETS_FILE, return_value=self.flow):
            with self.assertRaisesMessage(CommandError, "refresh token"):
                self._call()
