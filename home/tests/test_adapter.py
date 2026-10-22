"""
Test the allauth account adapter
"""

import smtplib
from unittest import mock

import django.test
from allauth.account.adapter import DefaultAccountAdapter

from home.adapter import AccountAdapter


class AccountAdapterTestCase(django.test.SimpleTestCase):

    def test_send_mail_failure_is_logged_and_reraised(self):
        adapter = AccountAdapter()
        with mock.patch.object(DefaultAccountAdapter, "send_mail", side_effect=smtplib.SMTPException("down")):
            with self.assertLogs("home.adapter", level="ERROR") as logs:
                with self.assertRaises(smtplib.SMTPException):
                    adapter.send_mail("account/email/test", "user@sort.com", {})
        self.assertIn("user@sort.com", logs.output[0])
