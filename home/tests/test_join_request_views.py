"""
Test the organisation join request views: browsing organisations, submitting and
withdrawing a request, and an administrator's review queue.
"""

from http import HTTPStatus

from django.contrib.messages import constants as message_levels
from django.contrib.messages import get_messages
from django.core import mail
from django.test import override_settings
from django.urls import reverse

import SORT.test.test_case
from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from home.models import OrganisationJoinRequest, OrganisationMembership
from SORT.test.model_factory import (
    OrganisationFactory,
    OrganisationJoinRequestFactory,
    OrganisationMembershipFactory,
    UserFactory,
)
from SORT.test.model_factory.user.constants import PASSWORD


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class JoinRequestViewTestCase(SORT.test.test_case.ViewTestCase):
    """The requester-facing views: browse, submit, list and withdraw."""

    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory()
        self.admin_user = self.organisation.members.first()

    def message_texts(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    # --- get started ----------------------------------------------------------

    def test_get_started_requires_login(self):
        self.get("organisation_get_started", HTTPStatus.FOUND, login=False)

    def test_get_started_offers_both_routes_to_an_organisation(self):
        self.assertEqual(self.user.organisation_set.count(), 0)

        response = self.get("organisation_get_started")

        self.assertContains(response, reverse("organisation_browse"))
        self.assertContains(response, reverse("organisation_create"))

    def test_get_started_reports_a_pending_request(self):
        OrganisationJoinRequestFactory(user=self.user, organisation=self.organisation)

        response = self.get("organisation_get_started")

        self.assertContains(response, self.organisation.name)
        self.assertContains(response, reverse("join_requests_mine"))

    def test_get_started_redirects_a_user_who_has_an_organisation(self):
        OrganisationMembershipFactory(
            user=self.user, organisation=self.organisation, role=ROLE_ADMIN
        )

        response = self.get("organisation_get_started", HTTPStatus.FOUND)

        self.assertRedirects(response, reverse("myorganisation"))

    def test_organisation_required_views_redirect_to_get_started(self):
        """The whole point of the page: a user with no organisation — including
        one whose request is pending — must not be pushed straight into
        creating a duplicate organisation."""
        OrganisationJoinRequestFactory(user=self.user, organisation=self.organisation)

        response = self.get("myorganisation", HTTPStatus.FOUND)

        self.assertRedirects(response, reverse("organisation_get_started"))

    # --- browse ---------------------------------------------------------------

    def test_browse_requires_login(self):
        self.get("organisation_browse", HTTPStatus.FOUND, login=False)

    def test_browse_lists_organisations(self):
        response = self.get("organisation_browse")

        self.assertContains(response, self.organisation.name)
        self.assertContains(
            response, reverse("organisation_join_request", args=[self.organisation.pk])
        )

    def test_browse_is_reachable_by_a_user_with_no_organisation(self):
        """OrganisationRequiredMixin would bounce this user to
        organisation_create, so the browse view must not use it."""
        self.assertEqual(self.user.organisation_set.count(), 0)

        self.get("organisation_browse")

    def test_browse_search_filters_by_name(self):
        matching = OrganisationFactory(name="Sheffield Teaching Hospitals")
        other = OrganisationFactory(name="Leeds Community Healthcare")
        self.login()

        response = self.client.get(
            reverse("organisation_browse"), data={"q": "Sheffield"}
        )

        self.assertContains(response, matching.name)
        self.assertNotContains(response, other.name)

    def test_browse_shows_membership_and_pending_states(self):
        member_organisation = OrganisationFactory()
        OrganisationMembershipFactory(
            user=self.user, organisation=member_organisation, role=ROLE_ADMIN
        )
        pending_organisation = OrganisationFactory()
        OrganisationJoinRequestFactory(
            user=self.user, organisation=pending_organisation
        )

        response = self.get("organisation_browse")

        self.assertContains(response, "Already a member")
        self.assertContains(response, "Request pending")
        self.assertNotContains(
            response,
            reverse("organisation_join_request", args=[member_organisation.pk]),
        )
        self.assertNotContains(
            response,
            reverse("organisation_join_request", args=[pending_organisation.pk]),
        )

    def test_browse_is_paginated(self):
        OrganisationFactory.create_batch(12)

        response = self.get("organisation_browse")

        self.assertTrue(response.context["page_obj"].has_other_pages())
        self.assertEqual(len(response.context["organisations"]), 10)

    # --- submit ---------------------------------------------------------------

    def test_confirmation_page(self):
        response = self.get(
            "organisation_join_request", pk=self.organisation.pk
        )

        self.assertContains(response, self.organisation.name)
        self.assertContains(response, "Send request")

    def test_submit_join_request(self):
        response = self.post(
            "organisation_join_request",
            HTTPStatus.FOUND,
            pk=self.organisation.pk,
            data={"message": "I am a research nurse"},
        )

        self.assertRedirects(response, reverse("join_requests_mine"))
        join_request = OrganisationJoinRequest.objects.get()
        self.assertEqual(join_request.user, self.user)
        self.assertEqual(join_request.organisation, self.organisation)
        self.assertEqual(join_request.message, "I am a research nurse")
        self.assertTrue(join_request.is_pending)
        # The organisation's admin is notified.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.admin_user.email])

    def test_submit_join_request_without_message(self):
        self.post(
            "organisation_join_request",
            HTTPStatus.FOUND,
            pk=self.organisation.pk,
        )

        self.assertEqual(OrganisationJoinRequest.objects.count(), 1)

    def test_submit_duplicate_join_request(self):
        OrganisationJoinRequestFactory(user=self.user, organisation=self.organisation)

        response = self.post(
            "organisation_join_request",
            HTTPStatus.FOUND,
            pk=self.organisation.pk,
        )

        self.assertRedirects(response, reverse("join_requests_mine"))
        self.assertEqual(OrganisationJoinRequest.objects.count(), 1)
        self.assertEqual(mail.outbox, [])
        self.assertTrue(
            any("waiting for a decision" in text for text in self.message_texts(response))
        )

    def test_submit_join_request_for_own_organisation(self):
        OrganisationMembershipFactory(
            user=self.user, organisation=self.organisation, role=ROLE_PROJECT_MANAGER
        )

        response = self.post(
            "organisation_join_request",
            HTTPStatus.FOUND,
            pk=self.organisation.pk,
        )

        self.assertRedirects(response, reverse("organisation_browse"))
        self.assertFalse(OrganisationJoinRequest.objects.exists())
        self.assertTrue(
            any("already a member" in text for text in self.message_texts(response))
        )

    def test_submit_join_request_for_unknown_organisation(self):
        self.post(
            "organisation_join_request", HTTPStatus.NOT_FOUND, pk=999999
        )

    # --- my requests ----------------------------------------------------------

    def test_my_requests_lists_own_requests_only(self):
        own = OrganisationJoinRequestFactory(
            user=self.user, organisation=self.organisation
        )
        someone_else = OrganisationJoinRequestFactory()

        response = self.get("join_requests_mine")

        self.assertEqual(list(response.context["join_requests"]), [own])
        self.assertContains(response, own.organisation.name)
        self.assertNotContains(response, someone_else.organisation.name)

    def test_withdraw_own_request(self):
        join_request = OrganisationJoinRequestFactory(
            user=self.user, organisation=self.organisation
        )

        response = self.post(
            "join_request_withdraw", HTTPStatus.FOUND, pk=join_request.pk
        )

        self.assertRedirects(response, reverse("join_requests_mine"))
        join_request.refresh_from_db()
        self.assertEqual(
            join_request.status, OrganisationJoinRequest.Status.WITHDRAWN
        )

    def test_cannot_withdraw_someone_elses_request(self):
        join_request = OrganisationJoinRequestFactory(organisation=self.organisation)

        self.post("join_request_withdraw", HTTPStatus.NOT_FOUND, pk=join_request.pk)

        join_request.refresh_from_db()
        self.assertTrue(join_request.is_pending)

    def test_withdraw_rejects_get(self):
        join_request = OrganisationJoinRequestFactory(
            user=self.user, organisation=self.organisation
        )

        self.get(
            "join_request_withdraw",
            HTTPStatus.METHOD_NOT_ALLOWED,
            pk=join_request.pk,
        )


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class JoinRequestReviewViewTestCase(SORT.test.test_case.ViewTestCase):
    """The administrator-facing review queue and decision actions.

    ViewTestCase.login() authenticates self.user, who is never the
    factory-created administrator, so these tests log in explicitly.
    """

    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory()
        self.admin_user = self.organisation.members.first()
        self.project_manager = OrganisationMembershipFactory(
            organisation=self.organisation, role=ROLE_PROJECT_MANAGER
        ).user
        self.requester = UserFactory()
        self.join_request = OrganisationJoinRequestFactory(
            user=self.requester,
            organisation=self.organisation,
            message="I am a research nurse",
        )

    def login_as(self, user):
        self.assertTrue(
            self.client.login(username=user.email, password=PASSWORD),
            "Authentication failed",
        )

    def message_levels(self, response):
        return [message.level for message in get_messages(response.wsgi_request)]

    # --- review queue ---------------------------------------------------------

    def test_queue_lists_pending_requests(self):
        self.login_as(self.admin_user)

        response = self.client.get(reverse("join_requests"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, str(self.requester))
        self.assertContains(response, "I am a research nurse")
        # Project Manager is pre-selected as the role to grant, and Admin is not.
        self.assertContains(
            response,
            f'<input class="form-check-input" type="radio" name="role" '
            f'value="{ROLE_PROJECT_MANAGER}" '
            f'id="role-{self.join_request.pk}-{ROLE_PROJECT_MANAGER}" checked>',
            html=True,
        )
        self.assertContains(
            response,
            f'<input class="form-check-input" type="radio" name="role" '
            f'value="{ROLE_ADMIN}" '
            f'id="role-{self.join_request.pk}-{ROLE_ADMIN}">',
            html=True,
        )

    def test_queue_hides_decided_requests_by_default(self):
        rejected = OrganisationJoinRequestFactory(
            organisation=self.organisation,
            status=OrganisationJoinRequest.Status.REJECTED,
        )
        self.login_as(self.admin_user)

        response = self.client.get(reverse("join_requests"))

        self.assertEqual(list(response.context["join_requests"]), [self.join_request])
        self.assertNotContains(response, str(rejected.user))

    def test_queue_shows_history_on_request(self):
        OrganisationJoinRequestFactory(
            organisation=self.organisation,
            status=OrganisationJoinRequest.Status.REJECTED,
        )
        self.login_as(self.admin_user)

        response = self.client.get(reverse("join_requests"), data={"status": "all"})

        self.assertEqual(len(response.context["join_requests"]), 2)

    def test_queue_denied_to_project_manager(self):
        self.login_as(self.project_manager)

        response = self.client.get(reverse("join_requests"))

        self.assertRedirects(response, reverse("members"))
        self.assertIn(message_levels.ERROR, self.message_levels(response))

    def test_queue_only_shows_the_active_organisations_requests(self):
        other_request = OrganisationJoinRequestFactory()
        self.login_as(self.admin_user)

        response = self.client.get(reverse("join_requests"))

        self.assertNotContains(response, str(other_request.user))

    # --- approve --------------------------------------------------------------

    def test_approve_with_default_role(self):
        self.login_as(self.admin_user)

        response = self.client.post(
            reverse("join_request_approve", args=[self.join_request.pk]),
            data={"role": ROLE_PROJECT_MANAGER},
        )

        self.assertRedirects(response, reverse("join_requests"))
        membership = OrganisationMembership.objects.get(
            user=self.requester, organisation=self.organisation
        )
        self.assertEqual(membership.role, ROLE_PROJECT_MANAGER)
        self.join_request.refresh_from_db()
        self.assertEqual(
            self.join_request.status, OrganisationJoinRequest.Status.APPROVED
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.requester.email])

    def test_approve_as_admin_role(self):
        self.login_as(self.admin_user)

        self.client.post(
            reverse("join_request_approve", args=[self.join_request.pk]),
            data={"role": ROLE_ADMIN},
        )

        membership = OrganisationMembership.objects.get(
            user=self.requester, organisation=self.organisation
        )
        self.assertEqual(membership.role, ROLE_ADMIN)

    def test_approve_with_invalid_role(self):
        self.login_as(self.admin_user)

        response = self.client.post(
            reverse("join_request_approve", args=[self.join_request.pk]),
            data={"role": "OWNER"},
        )

        self.assertRedirects(response, reverse("join_requests"))
        self.assertFalse(
            OrganisationMembership.objects.filter(
                user=self.requester, organisation=self.organisation
            ).exists()
        )
        self.join_request.refresh_from_db()
        self.assertTrue(self.join_request.is_pending)

    def test_approve_already_decided_request(self):
        self.join_request.status = OrganisationJoinRequest.Status.WITHDRAWN
        self.join_request.save()
        self.login_as(self.admin_user)

        response = self.client.post(
            reverse("join_request_approve", args=[self.join_request.pk]),
            data={"role": ROLE_PROJECT_MANAGER},
        )

        self.assertRedirects(response, reverse("join_requests"))
        self.assertIn(message_levels.INFO, self.message_levels(response))
        self.assertFalse(OrganisationMembership.objects.filter(
            user=self.requester, organisation=self.organisation
        ).exists())

    def test_approve_denied_to_project_manager(self):
        self.login_as(self.project_manager)

        response = self.client.post(
            reverse("join_request_approve", args=[self.join_request.pk]),
            data={"role": ROLE_PROJECT_MANAGER},
        )

        self.assertRedirects(response, reverse("members"))
        self.assertFalse(
            OrganisationMembership.objects.filter(
                user=self.requester, organisation=self.organisation
            ).exists()
        )

    def test_cannot_approve_another_organisations_request(self):
        """Permission is checked against the request's own organisation, not the
        session's active one, so an admin of one organisation cannot post a
        request id belonging to another."""
        other_request = OrganisationJoinRequestFactory()
        self.login_as(self.admin_user)

        response = self.client.post(
            reverse("join_request_approve", args=[other_request.pk]),
            data={"role": ROLE_PROJECT_MANAGER},
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(
            OrganisationMembership.objects.filter(
                user=other_request.user, organisation=other_request.organisation
            ).exists()
        )
        other_request.refresh_from_db()
        self.assertTrue(other_request.is_pending)

    def test_approve_rejects_get(self):
        self.login_as(self.admin_user)

        response = self.client.get(
            reverse("join_request_approve", args=[self.join_request.pk])
        )

        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    # --- reject ---------------------------------------------------------------

    def test_reject(self):
        self.login_as(self.admin_user)

        response = self.client.post(
            reverse("join_request_reject", args=[self.join_request.pk]),
            data={"note": "We can only add trust employees"},
        )

        self.assertRedirects(response, reverse("join_requests"))
        self.join_request.refresh_from_db()
        self.assertEqual(
            self.join_request.status, OrganisationJoinRequest.Status.REJECTED
        )
        self.assertEqual(
            self.join_request.decision_note, "We can only add trust employees"
        )
        self.assertFalse(
            OrganisationMembership.objects.filter(
                user=self.requester, organisation=self.organisation
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.requester.email])

    def test_reject_denied_to_project_manager(self):
        self.login_as(self.project_manager)

        response = self.client.post(
            reverse("join_request_reject", args=[self.join_request.pk])
        )

        self.assertRedirects(response, reverse("members"))
        self.join_request.refresh_from_db()
        self.assertTrue(self.join_request.is_pending)

    def test_reject_rejects_get(self):
        self.login_as(self.admin_user)

        response = self.client.get(
            reverse("join_request_reject", args=[self.join_request.pk])
        )

        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    # --- navigation badge -----------------------------------------------------

    def test_nav_badge_shown_to_admin(self):
        self.login_as(self.admin_user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.context["pending_join_request_count"], 1)
        self.assertContains(response, "pending join requests awaiting review")

    def test_nav_badge_hidden_from_project_manager(self):
        self.login_as(self.project_manager)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.context["pending_join_request_count"], 0)
        self.assertNotContains(response, "pending join requests awaiting review")
