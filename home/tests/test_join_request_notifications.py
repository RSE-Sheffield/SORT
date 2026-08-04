"""
Test the join request email notifications.

The project's default EMAIL_BACKEND is SMTP, so these tests must override it to
locmem in order to inspect django.core.mail.outbox.
"""

import smtplib
from unittest import mock

from django.core import mail
from django.test import RequestFactory, override_settings

import SORT.test.test_case
from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from home.models import OrganisationJoinRequest
from home.notifications import (
    get_organisation_admin_emails,
    notify_admins_of_join_request,
    notify_requester_of_join_decision,
)
from SORT.test.model_factory import (
    OrganisationFactory,
    OrganisationJoinRequestFactory,
    OrganisationMembershipFactory,
    UserFactory,
)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class JoinRequestNotificationTestCase(SORT.test.test_case.SORTTestCase):
    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory()
        self.admin_user = self.organisation.members.first()
        self.requester = UserFactory()
        self.join_request = OrganisationJoinRequestFactory(
            user=self.requester,
            organisation=self.organisation,
            message="I am a research nurse in Cardiology",
        )
        # "testserver" is the only host Django adds to ALLOWED_HOSTS during
        # tests, so absolute URLs must be built against it.
        self.request = RequestFactory().get("/", HTTP_HOST="testserver")

    # --- recipient resolution -------------------------------------------------

    def test_only_admins_are_notified(self):
        second_admin = OrganisationMembershipFactory(
            organisation=self.organisation, role=ROLE_ADMIN
        ).user
        project_manager = OrganisationMembershipFactory(
            organisation=self.organisation, role=ROLE_PROJECT_MANAGER
        ).user

        emails = get_organisation_admin_emails(self.organisation)

        self.assertCountEqual(
            emails, [self.admin_user.email, second_admin.email]
        )
        self.assertNotIn(project_manager.email, emails)

    def test_suspended_and_erased_admins_are_excluded(self):
        suspended = OrganisationMembershipFactory(
            organisation=self.organisation, role=ROLE_ADMIN
        ).user
        suspended.is_active = False
        suspended.save()
        erased = OrganisationMembershipFactory(
            organisation=self.organisation, role=ROLE_ADMIN
        ).user
        erased.email = "anon-1@deleted.invalid"
        erased.save()

        emails = get_organisation_admin_emails(self.organisation)

        self.assertEqual(emails, [self.admin_user.email])

    def test_admins_of_other_organisations_are_excluded(self):
        other_admin = OrganisationFactory().members.first()

        self.assertNotIn(
            other_admin.email, get_organisation_admin_emails(self.organisation)
        )

    # --- submission email -----------------------------------------------------

    def test_notify_admins_sends_one_email_per_admin(self):
        second_admin = OrganisationMembershipFactory(
            organisation=self.organisation, role=ROLE_ADMIN
        ).user

        sent = notify_admins_of_join_request(self.join_request, self.request)

        self.assertEqual(sent, 2)
        self.assertEqual(len(mail.outbox), 2)
        # One message per recipient, so administrators' addresses are not
        # disclosed to each other.
        for message in mail.outbox:
            self.assertEqual(len(message.to), 1)
            self.assertEqual(message.cc, [])
            self.assertEqual(message.bcc, [])
        self.assertCountEqual(
            [message.to[0] for message in mail.outbox],
            [self.admin_user.email, second_admin.email],
        )

    def test_notify_admins_email_content(self):
        notify_admins_of_join_request(self.join_request, self.request)

        message = mail.outbox[0]
        self.assertTrue(
            message.subject.startswith("[SORT] "),
            f"Unexpected subject: {message.subject!r}",
        )
        self.assertIn(str(self.requester), message.subject)
        self.assertIn(self.organisation.name, message.subject)
        self.assertIn(self.requester.email, message.body)
        self.assertIn("I am a research nurse in Cardiology", message.body)
        self.assertIn(
            "http://testserver/myorganisation/join-requests/", message.body
        )

    def test_notify_admins_without_a_request_uses_a_relative_link(self):
        with self.assertLogs("home.notifications", level="WARNING"):
            notify_admins_of_join_request(self.join_request)

        self.assertIn("/myorganisation/join-requests/", mail.outbox[0].body)

    def test_notify_admins_with_no_active_admins(self):
        self.admin_user.is_active = False
        self.admin_user.save()

        with self.assertLogs("home.notifications", level="WARNING"):
            sent = notify_admins_of_join_request(self.join_request, self.request)

        self.assertEqual(sent, 0)
        self.assertEqual(mail.outbox, [])

    def test_send_failure_is_logged_and_does_not_raise(self):
        with mock.patch(
            "home.notifications.send_mail", side_effect=smtplib.SMTPException("nope")
        ):
            with self.assertLogs("home.notifications", level="ERROR"):
                sent = notify_admins_of_join_request(self.join_request, self.request)

        self.assertEqual(sent, 0)

    # --- decision email -------------------------------------------------------

    def test_notify_requester_of_approval(self):
        self.join_request.status = OrganisationJoinRequest.Status.APPROVED
        self.join_request.granted_role = ROLE_PROJECT_MANAGER
        self.join_request.save()

        sent = notify_requester_of_join_decision(self.join_request, self.request)

        self.assertEqual(sent, 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.requester.email])
        self.assertIn("approved", message.subject.lower())
        self.assertIn("Project Manager", message.body)
        self.assertIn("http://testserver/dashboard/", message.body)

    def test_notify_requester_of_rejection(self):
        self.join_request.status = OrganisationJoinRequest.Status.REJECTED
        self.join_request.decision_note = "We can only add trust employees"
        self.join_request.save()

        notify_requester_of_join_decision(self.join_request, self.request)

        message = mail.outbox[0]
        self.assertEqual(message.to, [self.requester.email])
        self.assertIn("rejected", message.subject.lower())
        self.assertIn("We can only add trust employees", message.body)
        self.assertNotIn("Project Manager", message.body)

    def test_decision_email_goes_only_to_the_requester(self):
        self.join_request.status = OrganisationJoinRequest.Status.APPROVED
        self.join_request.granted_role = ROLE_PROJECT_MANAGER
        self.join_request.save()

        notify_requester_of_join_decision(self.join_request, self.request)

        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(self.admin_user.email, mail.outbox[0].to)
