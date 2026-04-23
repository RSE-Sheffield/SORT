"""
Unit tests for organisation views
"""

from http import HTTPStatus

import django.contrib.auth
import django.test
import django.urls

from home.models import Organisation
from SORT.test.model_factory import OrganisationFactory
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

    def test_organisation_view(self):
        self.get("myorganisation")
