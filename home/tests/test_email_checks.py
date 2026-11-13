"""
Test the email configuration system check (issue #754).
"""

from django.test import SimpleTestCase, override_settings

from home.checks.email import GMAIL_API_BACKEND, check_gmail_api_settings

COMPLETE_GMAIL_API_SETTINGS = dict(
    EMAIL_BACKEND=GMAIL_API_BACKEND,
    GMAIL_API_CLIENT_ID="test-client-id",
    GMAIL_API_CLIENT_SECRET="test-client-secret",
    GMAIL_API_REFRESH_TOKEN="test-refresh-token",
)


class GmailApiSettingsCheckTestCase(SimpleTestCase):
    @override_settings(**COMPLETE_GMAIL_API_SETTINGS)
    def test_complete_settings_pass(self):
        self.assertEqual(check_gmail_api_settings(None), [])

    @override_settings(
        **{**COMPLETE_GMAIL_API_SETTINGS, "GMAIL_API_REFRESH_TOKEN": None}
    )
    def test_missing_setting_is_an_error(self):
        errors = check_gmail_api_settings(None)

        self.assertEqual([error.id for error in errors], ["home.E004"])
        self.assertIn("DJANGO_GMAIL_API_REFRESH_TOKEN", errors[0].hint)
        self.assertNotIn("DJANGO_GMAIL_API_CLIENT_ID", errors[0].hint)

    @override_settings(
        EMAIL_BACKEND=GMAIL_API_BACKEND,
        GMAIL_API_CLIENT_ID="",
        GMAIL_API_CLIENT_SECRET=None,
        GMAIL_API_REFRESH_TOKEN=None,
    )
    def test_error_lists_every_missing_setting(self):
        (error,) = check_gmail_api_settings(None)

        for env_var in (
            "DJANGO_GMAIL_API_CLIENT_ID",
            "DJANGO_GMAIL_API_CLIENT_SECRET",
            "DJANGO_GMAIL_API_REFRESH_TOKEN",
        ):
            self.assertIn(env_var, error.hint)

    def test_other_backends_are_not_checked(self):
        for backend in (
            "django.core.mail.backends.smtp.EmailBackend",
            "django.core.mail.backends.locmem.EmailBackend",
        ):
            with self.subTest(backend=backend):
                with override_settings(
                    EMAIL_BACKEND=backend, GMAIL_API_CLIENT_ID=None
                ):
                    self.assertEqual(check_gmail_api_settings(None), [])
