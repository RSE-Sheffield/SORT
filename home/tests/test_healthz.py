from http import HTTPStatus
from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.urls import reverse


class HealthzViewTestCase(TestCase):
    """Tests for the /healthz/ health-check endpoint (issue #772)."""

    def test_ok_for_anonymous_user(self):
        response = self.client.get(reverse("healthz"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_head_allowed(self):
        self.assertEqual(self.client.head("/healthz/").status_code, HTTPStatus.OK)

    def test_database_failure_returns_503(self):
        with patch.object(connection, "cursor", side_effect=Exception("db down")):
            with self.assertLogs("SORT.views", level="ERROR"):
                response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertEqual(response.json(), {"status": "error"})
        self.assertNotIn("db down", response.content.decode())

    def test_post_not_allowed(self):
        response = self.client.post("/healthz/")
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)
