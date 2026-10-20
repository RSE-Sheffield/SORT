"""
Unit tests for organisation views
"""

from http import HTTPStatus

import django.contrib.auth
import django.contrib.messages
import django.test
import django.urls

from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from home.models import Organisation, OrganisationMembership
from SORT.test.model_factory import OrganisationFactory, OrganisationMembershipFactory
from SORT.test.model_factory.user.constants import PASSWORD
from SORT.test.test_case import ViewTestCase


class OrganisationViewTestCase(ViewTestCase):
    """
    Test organisation views
    """

    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory()

    def test_organisation_create_get(self):
        """
        Load the "Create an Organisation" form page
        """
        self.get("organisation_create")

    def test_organisation_create_post(self):
        """
        Test submitting the form to create a new organisation.
        """
        self.login_superuser()

        org = dict(
            name="My test org",
            description="My test description",
        )

        response = self.client.post(
            path=django.urls.reverse("organisation_create"),
            data=org,
        )

        # Expect to be redirected to organisation view
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        self.assertTrue(
            Organisation.objects.filter(name=org["name"]).exists(),
            "No organisations exist",
        )
        self.assertEqual(
            Organisation.objects.filter(name=org["name"]).count(),
            1,
            "No organisation created",
        )

    def test_organisation_edit_get(self):
        """
        An organisation admin can load the "Edit Organisation" form.
        """
        admin = self.organisation.members.first()
        self.assertTrue(
            self.client.login(username=admin.email, password=PASSWORD),
            "Authentication failed",
        )

        response = self.client.get(django.urls.reverse("organisation_edit"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, self.organisation.name)
        # The description is multi-line and must render as a <textarea>
        self.assertContains(response, "<textarea")

    def test_organisation_edit_post(self):
        """
        An organisation admin can rename the organisation and change its description.
        """
        admin = self.organisation.members.first()
        self.assertTrue(
            self.client.login(username=admin.email, password=PASSWORD),
            "Authentication failed",
        )

        response = self.client.post(
            path=django.urls.reverse("organisation_edit"),
            data=dict(name="Renamed org", description="Updated description"),
        )

        # Expect to be redirected to the organisation dashboard
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        self.organisation.refresh_from_db()
        self.assertEqual(self.organisation.name, "Renamed org")
        self.assertEqual(self.organisation.description, "Updated description")

    def test_organisation_edit_permission_denied(self):
        """
        A non-admin member (project manager) cannot edit the organisation.
        """
        original_name = self.organisation.name
        admin = self.organisation.members.first()
        OrganisationMembership.objects.create(
            user=self.user,
            organisation=self.organisation,
            role=ROLE_PROJECT_MANAGER,
            added_by=admin,
        )
        self.login()

        response = self.client.post(
            path=django.urls.reverse("organisation_edit"),
            data=dict(name="Hacked name", description="Should not be saved"),
        )

        # The project manager is redirected to the dashboard without saving
        self.assertRedirects(response, django.urls.reverse("myorganisation"))
        self.organisation.refresh_from_db()
        self.assertEqual(self.organisation.name, original_name)

    def test_organisation_create_when_already_a_member(self):
        """
        A user can create a second organisation even though they already
        belong to one (issue #675), but their active organisation is not
        silently switched to the new one (issue #682) - their existing
        organisation stays active, and they're told how to switch to the
        new one.
        """
        OrganisationMembershipFactory(
            user=self.user, organisation=self.organisation, role=ROLE_ADMIN
        )
        self.login()

        response = self.client.post(
            path=django.urls.reverse("organisation_create"),
            data=dict(name="My second org", description=""),
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(Organisation.objects.filter(name="My second org").exists())

        messages = list(django.contrib.messages.get_messages(response.wsgi_request))
        self.assertTrue(
            any("switcher" in str(message) for message in messages),
            "Expected a message explaining how to switch to the new organisation",
        )

        # The user's original organisation is still active - not silently
        # switched to the newly created one.
        dashboard_response = self.client.get(django.urls.reverse("myorganisation"))
        self.assertContains(dashboard_response, self.organisation.name)

    def test_organisation_create_when_not_already_a_member(self):
        """
        A user with no existing organisation has their newly created
        organisation set as active, as before (issue #682).
        """
        self.login()

        response = self.client.post(
            path=django.urls.reverse("organisation_create"),
            data=dict(name="My first org", description=""),
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        new_organisation = Organisation.objects.get(name="My first org")

        dashboard_response = self.client.get(django.urls.reverse("myorganisation"))
        self.assertContains(dashboard_response, new_organisation.name)

    def test_organisation_view(self):
        self.skipTest("Not yet implemented")


class SetActiveOrganisationViewTestCase(ViewTestCase):
    """Tests for the org-switcher view (issue #675)."""

    def setUp(self):
        super().setUp()
        self.first_organisation = OrganisationFactory()
        self.second_organisation = OrganisationFactory()
        OrganisationMembershipFactory(
            user=self.user, organisation=self.first_organisation, role=ROLE_ADMIN
        )
        OrganisationMembershipFactory(
            user=self.user, organisation=self.second_organisation, role=ROLE_ADMIN
        )

    def test_switch_to_a_member_organisation(self):
        self.login()

        response = self.client.post(
            django.urls.reverse("organisation_switch"),
            data={"organisation_id": self.second_organisation.pk},
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        dashboard_response = self.client.get(django.urls.reverse("myorganisation"))
        self.assertContains(
            dashboard_response, f"<h1>{self.second_organisation.name}</h1>"
        )
        self.assertNotContains(
            dashboard_response, f"<h1>{self.first_organisation.name}</h1>"
        )

    def test_cannot_switch_to_an_organisation_not_a_member_of(self):
        other_organisation = OrganisationFactory()
        self.login()

        response = self.client.post(
            django.urls.reverse("organisation_switch"),
            data={"organisation_id": other_organisation.pk},
        )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_switch_requires_login(self):
        response = self.client.post(
            django.urls.reverse("organisation_switch"),
            data={"organisation_id": self.first_organisation.pk},
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(django.urls.reverse("login"), response.url)

    def test_switcher_not_shown_for_single_organisation_user(self):
        OrganisationMembership.objects.filter(
            user=self.user, organisation=self.second_organisation
        ).delete()
        self.login()

        response = self.client.get(django.urls.reverse("myorganisation"))

        self.assertNotContains(response, "orgSwitcherDropdown")

    def test_switcher_shown_for_multi_organisation_user(self):
        self.login()

        response = self.client.get(django.urls.reverse("myorganisation"))

        self.assertContains(response, "orgSwitcherDropdown")
        self.assertContains(response, self.first_organisation.name)
        self.assertContains(response, self.second_organisation.name)

    def test_switch_redirects_to_safe_next_url(self):
        self.login()

        response = self.client.post(
            django.urls.reverse("organisation_switch"),
            data={
                "organisation_id": self.second_organisation.pk,
                "next": "/projects/",
            },
        )

        self.assertRedirects(
            response, "/projects/", fetch_redirect_response=False
        )

    def test_switch_ignores_unsafe_next_url(self):
        """An off-site `next` value must not be used as a redirect target (CWE-601)."""
        self.login()

        response = self.client.post(
            django.urls.reverse("organisation_switch"),
            data={
                "organisation_id": self.second_organisation.pk,
                "next": "https://evil.example.com/phishing",
            },
        )

        self.assertRedirects(response, django.urls.reverse("myorganisation"))
