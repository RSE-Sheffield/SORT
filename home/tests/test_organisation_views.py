"""
Unit tests for organisation views
"""

from http import HTTPStatus

import django.contrib.auth
import django.test
import django.urls

from home.models import Organisation

from .constants import PASSWORD
from .model_factory import OrganisationFactory

User = django.contrib.auth.get_user_model()


class OrganisationViewTestCase(django.test.TestCase):
    """
    Test organisation views
    """

    def setUp(self):
        self.user = User.objects.create_user(
            first_name='John',
            last_name='Smith',
            email='john.smith@sheffield.ac.uk',
            password=PASSWORD,
        )
        self.superuser = User.objects.create_superuser(
            first_name='Janet',
            last_name='Thompson',
            email='janet.thompson@sheffield.ac.uk',
            password=PASSWORD,
        )
        self.organisation = OrganisationFactory()

    def login(self):
        self.assertTrue(self.client.login(username=self.user.email, password=PASSWORD))

    def login_superuser(self):
        self.assertTrue(self.client.login(username=self.superuser.email, password=PASSWORD))

    def test_organisation_create_get(self):
        """
        Load the "Create an Organisation" form page
        """
        self.login()
        response = self.client.get(django.urls.reverse("organisation_create"))
        assert response.status_code == HTTPStatus.OK, response.status_code

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

        self.assertTrue(Organisation.objects.filter(name=org["name"]).exists(), "No organisations exist")
        self.assertEqual(Organisation.objects.filter(name=org["name"]).count(), 1, "No organisation created")

    def test_organisation_view(self):
        pass
