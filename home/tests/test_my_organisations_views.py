"""
Tests for the "My organisations" list and the self-service leave flow (issue #690).
"""

from http import HTTPStatus

import django.urls

from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from home.models import OrganisationMembership
from SORT.test.model_factory import OrganisationFactory, OrganisationMembershipFactory
from SORT.test.test_case import ViewTestCase


class MyOrganisationsListViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.admin_organisation = OrganisationFactory(name="Admin Org")
        self.manager_organisation = OrganisationFactory(name="Manager Org")
        OrganisationMembershipFactory(user=self.user, organisation=self.admin_organisation, role=ROLE_ADMIN)
        OrganisationMembershipFactory(user=self.user, organisation=self.manager_organisation, role=ROLE_PROJECT_MANAGER)
        self.other_organisation = OrganisationFactory(name="Not My Org")

    def test_lists_every_membership_with_role(self):
        """Each organisation the user belongs to is listed with their role in it."""
        response = self.get("my_organisations")

        self.assertContains(response, "Admin Org")
        self.assertContains(response, "Manager Org")
        self.assertContains(response, "Admin")
        self.assertContains(response, "Project Manager")
        self.assertNotContains(response, "Not My Org")

    def test_login_required(self):
        response = self.client.get(django.urls.reverse("my_organisations"))

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(django.urls.reverse("login"), response.url)

    def test_empty_state(self):
        OrganisationMembership.objects.filter(user=self.user).delete()

        response = self.get("my_organisations")

        self.assertContains(response, "You are not a member of any organisation yet")


class LeaveOrganisationViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        # OrganisationFactory creates its own ADMIN member, so self.user is never the sole admin here.
        self.organisation = OrganisationFactory(name="Leaving Org")
        self.other_organisation = OrganisationFactory(name="Staying Org")
        OrganisationMembershipFactory(user=self.user, organisation=self.organisation, role=ROLE_PROJECT_MANAGER)
        OrganisationMembershipFactory(user=self.user, organisation=self.other_organisation, role=ROLE_PROJECT_MANAGER)

    def url(self, organisation=None):
        return django.urls.reverse("organisation_leave", kwargs={"pk": (organisation or self.organisation).pk})

    def test_get_shows_confirmation(self):
        self.login()

        response = self.client.get(self.url())

        self.assertContains(response, "Leave Leaving Org")
        self.assertContains(response, "Project Manager")

    def test_post_leaves_organisation(self):
        self.login()

        response = self.client.post(self.url())

        self.assertRedirects(response, django.urls.reverse("my_organisations"), fetch_redirect_response=False)
        self.assertFalse(OrganisationMembership.objects.filter(user=self.user, organisation=self.organisation).exists())
        self.assertTrue(
            OrganisationMembership.objects.filter(user=self.user, organisation=self.other_organisation).exists()
        )

    def test_leaving_active_organisation_clears_session(self):
        self.login()
        self.client.post(django.urls.reverse("organisation_switch"), data={"organisation_id": self.organisation.pk})

        self.client.post(self.url())

        self.assertNotEqual(self.client.session.get("active_organisation_id"), self.organisation.pk)

    def test_leaving_last_organisation_redirects_to_get_started(self):
        OrganisationMembership.objects.filter(user=self.user, organisation=self.other_organisation).delete()
        self.login()

        response = self.client.post(self.url())

        self.assertRedirects(response, django.urls.reverse("organisation_get_started"), fetch_redirect_response=False)

    def test_sole_admin_cannot_leave(self):
        """The only administrator of an organisation with other members is blocked."""
        OrganisationMembership.objects.filter(organisation=self.organisation, role=ROLE_ADMIN).delete()
        OrganisationMembership.objects.filter(user=self.user, organisation=self.organisation).update(role=ROLE_ADMIN)
        OrganisationMembershipFactory(organisation=self.organisation, role=ROLE_PROJECT_MANAGER)
        self.login()

        get_response = self.client.get(self.url())
        post_response = self.client.post(self.url())

        self.assertContains(get_response, "You are the only administrator")
        self.assertRedirects(post_response, self.url(), fetch_redirect_response=False)
        self.assertTrue(OrganisationMembership.objects.filter(user=self.user, organisation=self.organisation).exists())

    def test_non_member_gets_404(self):
        stranger_organisation = OrganisationFactory(name="Stranger Org")
        self.login()

        self.assertEqual(self.client.get(self.url(stranger_organisation)).status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(self.client.post(self.url(stranger_organisation)).status_code, HTTPStatus.NOT_FOUND)

    def test_login_required(self):
        response = self.client.post(self.url())

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(django.urls.reverse("login"), response.url)
