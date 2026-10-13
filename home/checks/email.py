"""
Email configuration system checks.

Run with: python manage.py check
"""

from django.conf import settings
from django.core.checks import Error, register

GMAIL_API_BACKEND = "gmailapi_backend.mail.GmailBackend"

# Settings the Gmail API backend needs, mapped to the environment variables
# that set them in SORT/settings.py
GMAIL_API_REQUIRED_SETTINGS = {
    "GMAIL_API_CLIENT_ID": "DJANGO_GMAIL_API_CLIENT_ID",
    "GMAIL_API_CLIENT_SECRET": "DJANGO_GMAIL_API_CLIENT_SECRET",
    "GMAIL_API_REFRESH_TOKEN": "DJANGO_GMAIL_API_REFRESH_TOKEN",
}


@register()
def check_gmail_api_settings(app_configs, **kwargs):
    """
    Verify the OAuth2 credentials are set when the Gmail API backend is used.

    Without them the backend only fails when it first tries to send an email,
    so catch the problem at deployment time instead.
    """
    if settings.EMAIL_BACKEND != GMAIL_API_BACKEND:
        return []

    missing = [
        env_var
        for setting, env_var in GMAIL_API_REQUIRED_SETTINGS.items()
        if not getattr(settings, setting, None)
    ]
    if not missing:
        return []

    return [
        Error(
            "The Gmail API email backend is enabled but its OAuth2 credentials "
            "are incomplete.",
            hint=(
                f"Set {', '.join(missing)} in the .env file. "
                "See 'Email settings' in docs/deployment.md."
            ),
            id="home.E004",
        )
    ]
