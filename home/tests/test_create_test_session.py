import json
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase


class CreateTestSessionTests(TestCase):
    def run_command(self, **kwargs):
        out = StringIO()
        call_command("create_test_session", stdout=out, **kwargs)
        return json.loads(out.getvalue())

    def test_session_authenticates_test_user(self):
        data = self.run_command(email="a11y@example.com")
        self.assertEqual(data["user_email"], "a11y@example.com")
        self.client.cookies["sessionid"] = data["session_key"]
        response = self.client.get("/profile/")
        self.assertEqual(response.status_code, 200, response.get("Location"))

    def test_user_is_reused(self):
        self.run_command()
        self.run_command()
        self.assertEqual(get_user_model().objects.filter(email="a11y_test@sort.com").count(), 1)
