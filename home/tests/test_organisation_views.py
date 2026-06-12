"""
Unit tests for organisation views
"""

from http import HTTPStatus

import django.contrib.auth
import django.test
import django.urls

from home.constants import ROLE_PROJECT_MANAGER
from home.models import Organisation, OrganisationMembership
from SORT.test.model_factory import OrganisationFactory
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

        # The project manager is redirected away without saving any changes
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.organisation.refresh_from_db()
        self.assertEqual(self.organisation.name, original_name)

    def test_organisation_view(self):
        self.skipTest("Not yet implemented")
