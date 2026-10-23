from django.core import mail
from django.test import TestCase, override_settings
from django.urls import path

from SORT.logging import ThrottleFilter


def boom(request):
    raise RuntimeError("boom")


urlpatterns = [path("boom/", boom)]


@override_settings(ROOT_URLCONF=__name__, DEBUG=False)
class ErrorEmailTests(TestCase):
    def setUp(self):
        ThrottleFilter.reset()
        self.client.raise_request_exception = False

    @override_settings(ADMINS=[("Admin", "admin@example.com")])
    def test_500_emails_admins(self):
        self.assertEqual(self.client.get("/boom/").status_code, 500)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@example.com"])
        self.assertIn("boom", mail.outbox[0].body)

    @override_settings(ADMINS=[("Admin", "admin@example.com")])
    def test_repeated_errors_throttled(self):
        self.client.get("/boom/")
        self.client.get("/boom/")
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(ADMINS=[])
    def test_no_email_without_admins(self):
        self.client.get("/boom/")
        self.assertEqual(len(mail.outbox), 0)
