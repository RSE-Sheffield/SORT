"""
Management command to create a test user and generate a session cookie for accessibility testing.
This is used in CI/CD to allow Pa11y and Lighthouse to test authenticated pages.
"""
import json
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a test user and generate session cookie for accessibility testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            default="a11y_test@sort.com",
            help="Email for the test user",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="a11y_test_password_123",
            help="Password for the test user",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"]
        password = options["password"]

        # Create or get test user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": "A11y",
                "last_name": "Test",
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created test user: {email}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Test user already exists: {email}')
            )

        # Create a session for this user
        session = SessionStore()
        session['_auth_user_id'] = str(user.pk)
        session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        session['_auth_user_hash'] = user.get_session_auth_hash()
        session.save()

        # Output session information as JSON for easy parsing
        session_data = {
            "session_key": session.session_key,
            "cookie_name": "sessionid",
            "cookie_value": session.session_key,
            "user_email": email,
            "user_id": user.pk,
        }

        self.stdout.write(json.dumps(session_data))
