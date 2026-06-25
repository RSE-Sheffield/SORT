from http import HTTPStatus

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from SORT.views import csrf_failure


class CsrfFailureViewTestCase(TestCase):
    """Tests for the custom CSRF_FAILURE_VIEW (issue #623)."""

    def setUp(self):
        self.factory = RequestFactory()

    def _make_request(self):
        request = self.factory.post("/survey_response/some-token")
        request.user = AnonymousUser()
        return request

    def test_renders_friendly_403(self):
        """The view renders the friendly retry page with a 403 status."""
        response = csrf_failure(self._make_request(), reason="REASON_NO_CSRF_COOKIE")

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        content = response.content.decode()
        self.assertIn("your submission could not be completed", content)
        # Django's raw CSRF page wording must not leak to participants.
        self.assertNotIn("CSRF verification failed", content)

    def test_logs_the_failure(self):
        """The view logs a warning including the reason and request path."""
        with self.assertLogs("SORT.views", level="WARNING") as cm:
            csrf_failure(self._make_request(), reason="REASON_NO_CSRF_COOKIE")

        self.assertEqual(len(cm.records), 1)
        message = cm.records[0].getMessage()
        self.assertIn("REASON_NO_CSRF_COOKIE", message)
        self.assertIn("/survey_response/some-token", message)
        self.assertIn("csrf_cookie_present=False", message)
