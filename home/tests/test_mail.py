"""
Test that email send failures are handled the same way whichever email backend
is in use: Django's SMTP backend or the Gmail API backend (issue #754).

The Gmail API tests run the real GmailBackend with its HTTP transport mocked,
so they check the exceptions the backend actually raises without network access.
"""

import base64
import email
import logging
import re
import smtplib
from unittest import mock

import google.auth.exceptions
import googleapiclient.errors
import httplib2
from django.test import SimpleTestCase, override_settings

from home.adapter import AccountAdapter
from home.notifications import send_templated_mail

GMAIL_API_SETTINGS = dict(
    EMAIL_BACKEND="gmailapi_backend.mail.GmailBackend",
    GMAIL_API_CLIENT_ID="test-client-id",
    GMAIL_API_CLIENT_SECRET="test-client-secret",
    GMAIL_API_REFRESH_TOKEN="test-refresh-token",
    GMAIL_API_USER_ID="me",
)


def gmail_batch_response(status: str, body: str, sent: list):
    """
    Make a fake httplib2.Http.request that answers the Gmail API batch request.

    Every message in the batch gets the same HTTP status and JSON body. The
    raw message of each request is decoded and appended to ``sent``.
    """

    def request(self, uri, method="GET", body_=None, headers=None, **kwargs):
        batch_body = kwargs.get("body", body_)
        for raw in re.findall(r'"raw": "([^"]+)"', batch_body):
            sent.append(email.message_from_bytes(base64.urlsafe_b64decode(raw)))
        content_ids = re.findall(r"Content-ID: <([^>]+)>", batch_body)
        parts = "".join(
            f"--BOUNDARY\r\nContent-Type: application/http\r\n"
            f"Content-ID: <response-{content_id}>\r\n\r\n"
            f"HTTP/1.1 {status}\r\nContent-Type: application/json\r\n\r\n{body}\r\n"
            for content_id in content_ids
        )
        response = httplib2.Response(
            {"status": 200, "content-type": "multipart/mixed; boundary=BOUNDARY"}
        )
        return response, f"{parts}--BOUNDARY--".encode()

    return request


@override_settings(**GMAIL_API_SETTINGS)
@mock.patch("home.notifications.render_email", return_value=("Subject", "Body"))
class GmailApiBackendTestCase(SimpleTestCase):
    def setUp(self):
        # Silence the Google libraries' own request and error logging
        for name in ("gmailapi_backend", "googleapiclient", "google_auth_httplib2"):
            logger = logging.getLogger(name)
            self.addCleanup(setattr, logger, "disabled", logger.disabled)
            logger.disabled = True

    def send(self):
        return send_templated_mail(
            subject_template="unused",
            body_template="unused",
            context={},
            recipient_list=["user0@sort.com", "user1@sort.com"],
        )

    def test_sends_one_message_per_recipient(self, _render_email):
        sent = []
        with mock.patch.object(
            httplib2.Http,
            "request",
            gmail_batch_response("200 OK", '{"id": "1"}', sent),
        ):
            count = self.send()

        self.assertEqual(count, 2)
        self.assertEqual([m["To"] for m in sent], ["user0@sort.com", "user1@sort.com"])
        self.assertEqual(sent[0]["Subject"], "Subject")

    def test_api_error_is_logged_and_does_not_raise(self, _render_email):
        # e.g. the Gmail API is not enabled in the Google Cloud project
        error = '{"error": {"code": 403, "message": "Gmail API has not been used"}}'
        with mock.patch.object(
            httplib2.Http,
            "request",
            gmail_batch_response("403 Forbidden", error, []),
        ):
            with self.assertLogs("home.notifications", level="ERROR") as logs:
                count = self.send()

        self.assertEqual(count, 0)
        # Both recipients were attempted
        self.assertEqual(len(logs.records), 2)

    def test_revoked_refresh_token_is_logged_and_does_not_raise(self, _render_email):
        # Google answers 401, then refreshing the access token fails because
        # the refresh token was revoked
        unauthorised = (httplib2.Response({"status": 401}), b"")
        with mock.patch.object(httplib2.Http, "request", return_value=unauthorised):
            with mock.patch(
                "google.oauth2.credentials.Credentials.refresh",
                side_effect=google.auth.exceptions.RefreshError("invalid_grant"),
            ):
                with self.assertLogs("home.notifications", level="ERROR") as logs:
                    count = self.send()

        self.assertEqual(count, 0)
        self.assertIn("RefreshError", logs.output[0])


class AccountAdapterSendFailureTestCase(SimpleTestCase):
    """The allauth adapter logs send failures and re-raises them."""

    def test_send_errors_are_logged_and_reraised(self):
        errors = [
            smtplib.SMTPException("cannot connect"),
            OSError("network unreachable"),
            google.auth.exceptions.RefreshError("invalid_grant"),
            googleapiclient.errors.HttpError(
                httplib2.Response({"status": 403}), b"forbidden"
            ),
            httplib2.ServerNotFoundError("gmail.googleapis.com"),
        ]
        adapter = AccountAdapter()
        for error in errors:
            with self.subTest(error=type(error).__name__):
                with mock.patch(
                    "allauth.account.adapter.DefaultAccountAdapter.send_mail",
                    side_effect=error,
                ):
                    with self.assertLogs("home.adapter", level="ERROR"):
                        with self.assertRaises(type(error)):
                            adapter.send_mail(
                                "account/email/email_confirmation",
                                "user0@sort.com",
                                {},
                            )

    def test_programming_errors_are_not_logged_as_send_failures(self):
        with mock.patch(
            "allauth.account.adapter.DefaultAccountAdapter.send_mail",
            side_effect=KeyError("missing"),
        ):
            with self.assertNoLogs("home.adapter", level="ERROR"):
                with self.assertRaises(KeyError):
                    AccountAdapter().send_mail("prefix", "user0@sort.com", {})
