"""
Create a test user and print a session key for accessibility testing in CI.

Pa11y uses the session key to visit pages that require authentication.
"""

import json

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY, get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a test user and print a JSON session key for accessibility testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default="a11y_test@sort.com",
            help="Email for the test user",
        )

    def handle(self, *args, **options):
        user, _ = get_user_model().objects.get_or_create(
            email=options["email"],
            defaults={"is_active": True},
        )
        # The session is the only credential, so the password is never needed
        user.set_unusable_password()
        user.save()

        session = SessionStore()
        session[SESSION_KEY] = str(user.pk)
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()

        # Only JSON on stdout so the output can be parsed directly
        self.stdout.write(json.dumps({"session_key": session.session_key, "user_email": user.email}))
